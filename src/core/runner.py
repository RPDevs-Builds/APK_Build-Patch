"""
Unified Pipeline Orchestration Engine.
Coordinates fetchers, patchers, builders, metadata extractors, and storage/distribution generators.
"""

import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config_loader import ConfigLoader, load_config
from .logger import log_end_step, log_error, log_info, log_step, log_success, log_warn
from .utils import calculate_sha256
from ..fetchers.apkmirror import APKMirrorFetcher
from ..fetchers.playstore import PlayStoreFetcher
from ..fetchers.uptodown import UptodownFetcher
from ..fetchers.archive import ArchiveFetcher
from ..fetchers.direct import DirectFetcher
from ..patchers.revanced_patcher import ReVancedPatcher
from ..builders.gradle_builder import GradleBuilder
from ..builders.flutter_builder import FlutterBuilder
from ..builders.react_native_builder import ReactNativeBuilder
from ..storage.apk_metadata import APKMetadataExtractor, APKMetadata
from ..storage.fdroid_generator import FDroidGenerator
from ..storage.obtainium_generator import ObtainiumGenerator
from ..storage.web_portal_generator import WebPortalGenerator
from ..storage.magisk_update_generator import MagiskUpdateGenerator
from ..storage.release_publisher import ReleasePublisher

class PipelineRunner:
    def __init__(self, config_dir: Optional[Path | str] = None):
        self.config_loader = load_config(config_dir)
        self.base_dir = self.config_loader.config_dir.parent
        self.temp_dir = self.base_dir / "temp"
        self.dist_dir = self.base_dir / "dist"
        self.apks_dir = self.dist_dir / "apks"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.apks_dir.mkdir(parents=True, exist_ok=True)

        # Initialize subcomponents
        sources_cfg = self.config_loader.get_sources_config()
        self.fetchers = {
            "apkmirror": APKMirrorFetcher(sources_cfg.get("apkmirror")),
            "playstore": PlayStoreFetcher(sources_cfg.get("playstore")),
            "uptodown": UptodownFetcher(sources_cfg.get("uptodown")),
            "archive": ArchiveFetcher(sources_cfg.get("archive")),
            "direct": DirectFetcher(),
        }
        self.patcher = ReVancedPatcher(temp_dir=self.temp_dir)
        self.gradle_builder = GradleBuilder(workspace_dir=self.temp_dir / "repos")
        self.flutter_builder = FlutterBuilder(workspace_dir=self.temp_dir / "repos")
        self.rn_builder = ReactNativeBuilder(workspace_dir=self.temp_dir / "repos")
        self.metadata_extractor = APKMetadataExtractor()

    def fetch_base_apk(self, app_cfg: Dict[str, Any]) -> Optional[Path]:
        """Fetch stock APK using prioritized fallback sources."""
        app_name = app_cfg.get("app_name", "App")
        pkg_name = app_cfg.get("pkg_name", "")
        version = app_cfg.get("version", "auto")
        arch = app_cfg.get("arch", "all")
        dpi = app_cfg.get("dpi", "nodpi")

        dest_stock = self.temp_dir / f"{pkg_name or app_name}_{version}_{arch}.apk"
        if dest_stock.exists():
            log_info(f"Using cached base APK: {dest_stock}")
            return dest_stock

        sources_cfg = self.config_loader.get_sources_config()
        priorities = sources_cfg.get("priorities", {}).get("order", ["apkmirror", "playstore", "uptodown", "archive", "direct"])

        for source_key in priorities:
            fetcher = self.fetchers.get(source_key)
            if not fetcher:
                continue

            dl_key = f"{source_key}_dlurl"
            target_loc = app_cfg.get(dl_key)
            if source_key == "playstore":
                target_loc = app_cfg.get("playstore_pkg") or pkg_name

            if not target_loc:
                continue

            log_info(f"Attempting to fetch {app_name} from {source_key.upper()} ({target_loc})...")
            try:
                # If version is auto, resolve latest available
                resolved_ver = version
                if version in ("auto", "latest"):
                    vers = fetcher.get_latest_versions(target_loc)
                    if vers:
                        resolved_ver = vers[0]

                success = fetcher.download_apk(target_loc, resolved_ver, dest_stock, arch=arch, dpi=dpi)
                if success:
                    for ext in [".apk", ".xapk", ".apkm", ".apks"]:
                        cand = dest_stock.with_suffix(ext)
                        if cand.exists():
                            log_success(f"Acquired base APK for {app_name} from {source_key.upper()}: {cand.name}")
                            return cand
            except Exception as e:
                log_warn(f"Failed to fetch from {source_key}: {e}")

        log_error(f"Could not fetch base APK for {app_name} from any configured source.")
        return None

    def run_patching_pipeline(self, target_app: Optional[str] = None) -> List[Dict[str, Any]]:
        """Run the ReVanced & Morphe patching pipeline for all or specific enabled apps."""
        patches_cfg = self.config_loader.get_patches_config()
        apps = patches_cfg.get("apps", {})
        results = []

        for name, app_cfg in apps.items():
            if target_app and target_app.lower() != name.lower():
                continue
            if not app_cfg.get("enabled", True):
                log_info(f"Skipping disabled patch target: {name}")
                continue

            log_step(f"Starting Patch Process: {name} ({app_cfg.get('app_name')})")
            try:
                stock_apk = self.fetch_base_apk(app_cfg)
                if not stock_apk:
                    log_error(f"Cannot patch {name}: Base APK not available.")
                    continue

                res = self.patcher.patch(
                    stock_apk=stock_apk,
                    output_dir=self.apks_dir,
                    app_cfg=app_cfg,
                )
                results.append(res)
                log_success(f"Successfully processed {name}")
            except Exception as e:
                log_error(f"Patching failed for {name}: {e}")
            finally:
                log_end_step()

        return results

    def run_repo_builds(self, target_repo: Optional[str] = None) -> List[Path]:
        """Clone and compile open source repositories from repos.toml or ad-hoc URL."""
        repos_cfg = self.config_loader.get_repos_config()
        repos = repos_cfg.get("repos", {})
        built_apks = []

        for name, repo_cfg in repos.items():
            if target_repo and target_repo.lower() != name.lower() and target_repo not in repo_cfg.get("repo_url", ""):
                continue
            if not repo_cfg.get("enabled", True):
                log_info(f"Skipping disabled repository: {name}")
                continue

            log_step(f"Starting Source Build: {name}")
            build_sys = repo_cfg.get("build_system", "gradle").lower()
            repo_url = repo_cfg.get("repo_url")
            branch = repo_cfg.get("branch", "main")

            try:
                if build_sys == "gradle":
                    apks = self.gradle_builder.build_from_source(repo_url, branch, self.apks_dir, repo_cfg)
                elif build_sys == "flutter":
                    apks = self.flutter_builder.build_from_source(repo_url, branch, self.apks_dir, repo_cfg)
                elif build_sys in ("react_native", "react-native"):
                    apks = self.rn_builder.build_from_source(repo_url, branch, self.apks_dir, repo_cfg)
                else:
                    log_error(f"Unknown build system '{build_sys}' for {name}")
                    continue

                built_apks.extend(apks)
                log_success(f"Successfully built {len(apks)} APKs from {name}")
            except Exception as e:
                log_error(f"Failed to build repository {name}: {e}")
            finally:
                log_end_step()

        return built_apks

    def generate_storage_hub(self, release_tag: str = "latest") -> Dict[str, Any]:
        """Extract metadata from all artifacts in dist/apks and generate F-Droid, Web Portal, Obtainium, and Magisk OTA."""
        log_step("Generating Ultimate APK Storage & Multi-Channel Distribution Hub...")
        storage_cfg = self.config_loader.get_storage_config()
        
        all_artifacts = list(self.apks_dir.glob("*.apk")) + list(self.apks_dir.glob("*.zip"))
        if not all_artifacts:
            log_warn("No APK or ZIP artifacts found in dist/apks to index.")
            return {}

        icons_dir = self.dist_dir / "icons"
        icons_dir.mkdir(parents=True, exist_ok=True)

        metadata_list: List[APKMetadata] = []
        for art in all_artifacts:
            try:
                meta = self.metadata_extractor.extract_metadata(art, icons_output_dir=icons_dir)
                metadata_list.append(meta)
            except Exception as e:
                log_warn(f"Could not extract metadata for {art.name}: {e}")

        # 1. F-Droid Repository
        fdroid_gen = FDroidGenerator(storage_cfg.get("fdroid"))
        fdroid_path = fdroid_gen.generate_repository(metadata_list)

        # 2. Obtainium Feed
        obtainium_gen = ObtainiumGenerator(storage_cfg.get("obtainium"))
        obtainium_path = obtainium_gen.generate_feed(metadata_list, release_tag)

        # 3. Static Web Portal & QR Codes
        web_gen = WebPortalGenerator(storage_cfg.get("web_portal"))
        web_path = web_gen.generate_portal(metadata_list, release_tag=release_tag)

        # 4. Magisk Root Module Update JSONs
        magisk_gen = MagiskUpdateGenerator(output_dir=self.dist_dir / "modules_ota")
        ota_files = magisk_gen.generate_update_jsons(metadata_list, release_tag=release_tag)

        log_success(f"Storage Hub generation complete! Indexed {len(metadata_list)} artifacts.")
        log_end_step()

        return {
            "metadata": metadata_list,
            "fdroid_dir": fdroid_path,
            "obtainium_file": obtainium_path,
            "web_portal_dir": web_path,
            "ota_files": ota_files,
        }
