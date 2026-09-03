"""
Magisk / KernelSU / APatch Module Update JSON Generator.
Generates <module-id>-update.json files for in-root-manager OTA updates.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.logger import log_success
from .apk_metadata import APKMetadata

class MagiskUpdateGenerator:
    def __init__(self, output_dir: Path | str = "dist/modules_ota"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_update_jsons(
        self,
        metadata_list: List[APKMetadata],
        github_repo: str = "RPDevs-Builds/APK_Build-Patch",
        release_tag: str = "latest",
        changelog_url: Optional[str] = None,
    ) -> List[Path]:
        generated = []
        cl_url = changelog_url or f"https://raw.githubusercontent.com/{github_repo}/main/docs/CHANGELOG.md"

        for meta in metadata_list:
            if not meta.is_module:
                continue

            # Strip 'module.' prefix if present
            mod_id = meta.package_name.replace("module.", "")
            json_filename = f"{mod_id}-update.json"
            json_path = self.output_dir / json_filename
            zip_dl_url = f"https://github.com/{github_repo}/releases/download/{release_tag}/{meta.filename}"

            payload = {
                "version": meta.version_name,
                "versionCode": meta.version_code,
                "zipUrl": zip_dl_url,
                "changelog": cl_url,
            }

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)

            generated.append(json_path)

        log_success(f"Generated {len(generated)} Magisk update JSONs in {self.output_dir}")
        return generated
