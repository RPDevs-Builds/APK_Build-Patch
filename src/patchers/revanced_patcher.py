"""
ReVanced & Morphe CLI Patcher Orchestrator.
"""

import json
import os
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import requests

from ..core.logger import log_error, log_info, log_step, log_success, log_warn
from ..core.utils import calculate_sha256, find_java, run_cmd
from .signer import APKSigner
from .split_merger import SplitMerger
from .magisk_packager import MagiskPackager

class ReVancedPatcher:
    def __init__(self, temp_dir: Path | str = "temp", bin_dir: Optional[Path | str] = None):
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.bin_dir = Path(bin_dir) if bin_dir else self.base_dir / "bin"
        self.java_bin = find_java("21")
        self.signer = APKSigner()
        self.merger = SplitMerger()
        self.packager = MagiskPackager()

    def get_github_release_asset(
        self,
        repo: str,
        tag: str = "latest",
        pattern: str = r"\.jar$",
        dest_dir: Optional[Path] = None,
    ) -> Optional[Path]:
        """Fetch prebuilt JAR or binary asset from a GitHub Release."""
        target_dir = dest_dir or (self.temp_dir / "prebuilts")
        target_dir.mkdir(parents=True, exist_ok=True)
        
        api_url = f"https://api.github.com/repos/{repo}/releases/latest" if tag == "latest" else f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
        headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "RPDevs-APK-Engine/1.0"}
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"

        try:
            resp = requests.get(api_url, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            assets = data.get("assets", [])
            for asset in assets:
                name = asset.get("name", "")
                if re.search(pattern, name) and not name.endswith(".asc") and not name.endswith(".json"):
                    dl_url = asset.get("browser_download_url")
                    out_path = target_dir / name
                    if out_path.exists():
                        return out_path
                    log_info(f"Downloading {name} from {repo} ({data.get('tag_name')})...")
                    with requests.get(dl_url, stream=True, timeout=120) as stream_resp:
                        stream_resp.raise_for_status()
                        with open(out_path, "wb") as f:
                            for chunk in stream_resp.iter_content(chunk_size=64 * 1024):
                                if chunk:
                                    f.write(chunk)
                    return out_path
        except Exception as e:
            log_warn(f"Failed to fetch GitHub asset from {repo}: {e}")
        return None

    def strip_unwanted_archs(self, input_apk: Path, target_arch: str) -> Path:
        """Strip native architecture libraries not matching target architecture."""
        if target_arch in ("all", "universal"):
            return input_apk

        stripped_apk = self.temp_dir / f"{input_apk.stem}_stripped.apk"
        shutil.copy2(input_apk, stripped_apk)
        
        arch_map = {
            "arm64-v8a": ["lib/armeabi-v7a/*", "lib/x86/*", "lib/x86_64/*"],
            "arm-v7a": ["lib/arm64-v8a/*", "lib/x86/*", "lib/x86_64/*"],
            "x86": ["lib/arm64-v8a/*", "lib/armeabi-v7a/*", "lib/x86_64/*"],
            "x86_64": ["lib/arm64-v8a/*", "lib/armeabi-v7a/*", "lib/x86/*"],
        }
        
        to_delete = arch_map.get(target_arch, [])
        if to_delete and shutil.which("zip"):
            try:
                cmd = ["zip", "-d", str(stripped_apk)] + to_delete
                run_cmd(cmd, check=False)
            except Exception as e:
                log_warn(f"Failed to strip unwanted libs with zip: {e}")
        return stripped_apk

    def patch(
        self,
        stock_apk: Path | str,
        output_dir: Path | str,
        app_cfg: Dict[str, Any],
        cli_jar: Optional[Path | str] = None,
        patches_jar: Optional[Path | str] = None,
    ) -> Dict[str, Any]:
        """Execute the ReVanced/Morphe patching workflow for an application."""
        stock = Path(stock_apk)
        out_d = Path(output_dir)
        out_d.mkdir(parents=True, exist_ok=True)

        app_name = app_cfg.get("app_name", "App")
        pkg_name = app_cfg.get("pkg_name", "")
        rv_brand = app_cfg.get("rv_brand", "ReVanced")
        arch = app_cfg.get("arch", "all")
        build_mode = app_cfg.get("build_mode", "both")

        # 1. Resolve CLI & Patches prebuilts
        cli_src = app_cfg.get("cli_source", "ReVanced/revanced-cli")
        patches_src = app_cfg.get("patches_source", "ReVanced/revanced-patches")
        cli_ver = app_cfg.get("cli_version", "latest")
        patches_ver = app_cfg.get("patches_version", "latest")

        cli_path = Path(cli_jar) if cli_jar else self.get_github_release_asset(cli_src, cli_ver, r"(cli|desktop).*\.jar$")
        patches_path = Path(patches_jar) if patches_jar else self.get_github_release_asset(patches_src, patches_ver, r"(patches|bundle).*\.(jar|rvp)$")

        if not cli_path or not cli_path.exists():
            raise RuntimeError(f"Could not locate ReVanced/Morphe CLI jar from {cli_src}")
        if not patches_path or not patches_path.exists():
            raise RuntimeError(f"Could not locate Patches bundle from {patches_src}")

        # 2. Check if stock input is a bundle and needs merging
        if str(stock).endswith(".apkm") or str(stock).endswith(".xapk"):
            merged_stock = self.temp_dir / f"{stock.stem}_merged.apk"
            if not self.merger.merge_bundle(stock, merged_stock):
                raise RuntimeError(f"Failed to merge split APK bundle: {stock}")
            stock = merged_stock

        # 3. Architecture library strip
        ready_stock = self.strip_unwanted_archs(stock, arch)

        # 4. Construct CLI patch command
        brand_slug = rv_brand.lower().replace(" ", "-")
        app_slug = app_name.lower().replace(" ", "-")
        patched_apk_name = f"{app_slug}-{brand_slug}-{arch}.apk"
        patched_apk = out_d / patched_apk_name

        cmd = [
            self.java_bin,
            "-jar",
            str(cli_path),
            "patch",
            str(ready_stock),
            "-o",
            str(patched_apk),
            "-p",
            str(patches_path),
            "--keystore",
            str(self.signer.keystore_path),
            "--keystore-entry-password",
            self.signer.keystore_pass.replace("pass:", ""),
            "--keystore-password",
            self.signer.keystore_pass.replace("pass:", ""),
            "--signer",
            self.signer.key_alias,
            "--keystore-entry-alias",
            self.signer.key_alias,
            "-t",
            str(self.temp_dir / f"rv_tmp_{app_slug}"),
        ]

        # Included / excluded patches
        for inc in app_cfg.get("included_patches", []):
            cmd.extend(["-e", inc])
        for exc in app_cfg.get("excluded_patches", []):
            cmd.extend(["-d", exc])

        if app_cfg.get("patcher_args"):
            extra_args = app_cfg["patcher_args"].split()
            cmd.extend(extra_args)

        log_step(f"Executing patcher for {app_name} ({rv_brand})...")
        try:
            res = run_cmd(cmd, check=True)
            log_success(f"Built patched non-root APK: {patched_apk.name}")
        except Exception as e:
            log_error(f"Patcher execution failed for {app_name}: {e}")
            raise

        results = {
            "non_root_apk": patched_apk,
            "sha256": calculate_sha256(patched_apk),
            "app_name": app_name,
            "package_name": pkg_name,
            "rv_brand": rv_brand,
            "arch": arch,
        }

        # 5. Build Magisk / KernelSU root module if requested
        if build_mode in ("module", "both"):
            module_name = f"{app_slug}-{brand_slug}-module-{arch}.zip"
            module_zip = out_d / module_name
            module_id = f"{app_slug}-{brand_slug}"
            self.packager.package_module(
                patched_apk=patched_apk,
                stock_apk=stock,
                output_zip=module_zip,
                module_id=module_id,
                module_name=f"{app_name} {rv_brand}",
                version_name=app_cfg.get("version", "v1.0.0"),
                version_code=1,
                author="RPDevs-Builds",
                description=f"{app_name} ({rv_brand}) Root Module",
                arch=arch,
            )
            results["magisk_module"] = module_zip

        return results
