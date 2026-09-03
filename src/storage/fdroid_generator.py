"""
F-Droid Repository Indexer & Metadata Generator.
Produces compliant F-Droid index-v1.jar and index-v2.json files for custom repo subscription.
"""

import hashlib
import json
import os
import shutil
import time
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.logger import log_error, log_info, log_step, log_success
from .apk_metadata import APKMetadata

class FDroidGenerator:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.repo_name = self.config.get("repo_name", "RPDevs APK Vault")
        self.repo_desc = self.config.get("repo_description", "Automated builds & patched APKs")
        self.repo_url = self.config.get("repo_url", "https://rpdevs-builds.github.io/APK_Build-Patch/fdroid/repo")
        self.output_dir = Path(self.config.get("output_dir", "dist/fdroid"))

    def generate_repository(self, metadata_list: List[APKMetadata]) -> Path:
        """Build F-Droid repo structure with index-v1.json, index-v1.jar, and index-v2.json."""
        repo_dir = self.output_dir / "repo"
        repo_dir.mkdir(parents=True, exist_ok=True)
        icons_dir = self.output_dir / "icons"
        icons_dir.mkdir(parents=True, exist_ok=True)

        timestamp = int(time.time())
        apps_dict = {}
        packages_dict = {}

        # F-Droid Index V2 structure
        v2_apps = {}
        v2_packages = {}

        for meta in metadata_list:
            if meta.is_module:
                continue # Skip Magisk modules in F-Droid APK index

            pkg = meta.package_name
            apk_filename = Path(meta.filepath).name

            # Copy APK into repo/
            dest_apk = repo_dir / apk_filename
            if Path(meta.filepath).exists() and not dest_apk.exists():
                shutil.copy2(meta.filepath, dest_apk)

            # Copy icon if available
            if meta.icon_path and (Path(meta.icon_path).exists() or (icons_dir / meta.icon_path).exists()):
                icon_src = Path(meta.icon_path) if Path(meta.icon_path).exists() else (icons_dir / meta.icon_path)
                dest_icon = icons_dir / f"{pkg}.png"
                if not dest_icon.exists():
                    shutil.copy2(icon_src, dest_icon)

            # 1. Apps entry
            if pkg not in apps_dict:
                apps_dict[pkg] = {
                    "packageName": pkg,
                    "name": meta.app_name,
                    "summary": meta.description or f"{meta.app_name} Android Application",
                    "description": meta.description or f"{meta.app_name} built and distributed by RPDevs Vault.",
                    "icon": f"{pkg}.png" if meta.icon_path else None,
                    "categories": [meta.category],
                    "added": timestamp * 1000,
                    "lastUpdated": timestamp * 1000,
                }
                v2_apps[pkg] = {
                    "categories": [meta.category],
                    "suggestedVersionCode": meta.version_code,
                    "name": {"en-US": meta.app_name},
                    "summary": {"en-US": meta.description or meta.app_name},
                    "description": {"en-US": meta.description or meta.app_name},
                }

            # 2. Packages entry
            pkg_entry = {
                "packageName": pkg,
                "versionName": meta.version_name,
                "versionCode": meta.version_code,
                "size": meta.size_bytes,
                "hash": meta.sha256,
                "hashType": "sha256",
                "minSdkVersion": meta.min_sdk,
                "targetSdkVersion": meta.target_sdk,
                "apkName": apk_filename,
                "nativecode": meta.architectures,
                "added": timestamp * 1000,
            }

            if pkg not in packages_dict:
                packages_dict[pkg] = []
                v2_packages[pkg] = {}

            packages_dict[pkg].append(pkg_entry)
            
            v2_packages[pkg][str(meta.version_code)] = {
                "versionName": meta.version_name,
                "versionCode": meta.version_code,
                "file": {
                    "name": f"/{apk_filename}",
                    "sha256": meta.sha256,
                    "size": meta.size_bytes,
                },
                "manifest": {
                    "minSdkVersion": meta.min_sdk,
                    "targetSdkVersion": meta.target_sdk,
                    "nativecode": meta.architectures,
                },
            }

        # index-v1.json payload
        index_v1 = {
            "repo": {
                "timestamp": timestamp,
                "version": 20002,
                "name": self.repo_name,
                "icon": "icon.png",
                "address": self.repo_url,
                "description": self.repo_desc,
            },
            "apps": list(apps_dict.values()),
            "packages": packages_dict,
        }

        # Write index-v1.json
        index_v1_path = repo_dir / "index-v1.json"
        with open(index_v1_path, "w", encoding="utf-8") as f:
            json.dump(index_v1, f, indent=2)

        # Write index-v1.jar (Zip archive containing index-v1.json)
        index_v1_jar = repo_dir / "index-v1.jar"
        with zipfile.ZipFile(index_v1_jar, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.write(index_v1_path, "index-v1.json")

        # Write modern index-v2.json
        index_v2 = {
            "repo": {
                "timestamp": timestamp * 1000,
                "name": {"en-US": self.repo_name},
                "description": {"en-US": self.repo_desc},
                "icon": {"en-US": {"name": "/icons/icon.png"}},
                "address": self.repo_url,
            },
            "packages": v2_packages,
        }
        index_v2_path = repo_dir / "index-v2.json"
        with open(index_v2_path, "w", encoding="utf-8") as f:
            json.dump(index_v2, f, indent=2)

        log_success(f"F-Droid repository generated at {repo_dir} with {len(metadata_list)} items.")
        return self.output_dir
