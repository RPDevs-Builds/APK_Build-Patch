"""
Obtainium App Feed & Catalog Generator.
Generates compliant Obtainium export JSON for 1-click importing and automatic updates.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.logger import log_success
from .apk_metadata import APKMetadata

class ObtainiumGenerator:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.feed_name = self.config.get("feed_name", "RPDevs APK Vault")
        self.output_file = Path(self.config.get("output_file", "dist/obtainium-feed.json"))
        self.github_repo = self.config.get("github_repository", "RPDevs-Builds/APK_Build-Patch")

    def generate_feed(self, metadata_list: List[APKMetadata], release_tag: str = "latest") -> Path:
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        apps = []
        for meta in metadata_list:
            if meta.is_module:
                continue
            
            # Construct Obtainium app entry
            app_entry = {
                "id": meta.package_name,
                "url": f"https://github.com/{self.github_repo}",
                "author": "RPDevs-Builds",
                "name": meta.app_name,
                "preferredApkIndex": 0,
                "additionalSettings": json.dumps({
                    "includeFilter": meta.filename,
                    "versionExtraction": "from_release_title",
                }),
                "overrideSource": "GitHub",
            }
            apps.append(app_entry)

        feed_data = {
            "name": self.feed_name,
            "version": 1,
            "apps": apps,
        }

        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(feed_data, f, indent=2)

        log_success(f"Obtainium feed generated at {self.output_file} ({len(apps)} apps)")
        return self.output_file
