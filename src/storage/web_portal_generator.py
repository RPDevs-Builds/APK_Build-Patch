"""
Web Portal & Static Catalog Generator.
Renders responsive HTML dashboard with category filters, live search, and mobile QR codes.
"""

import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
import qrcode

from ..core.logger import log_info, log_success
from .apk_metadata import APKMetadata

class WebPortalGenerator:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.title = self.config.get("title", "RPDevs APK Vault")
        self.output_dir = Path(self.config.get("output_dir", "dist/web"))
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.web_template_dir = self.base_dir / "web"

    def _generate_qr_code(self, data_url: str, output_path: Path) -> None:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(data_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#00e5ff", back_color="#121826")
        img.save(output_path)

    def generate_portal(
        self,
        metadata_list: List[APKMetadata],
        github_repo: str = "RPDevs-Builds/APK_Build-Patch",
        release_tag: str = "latest",
    ) -> Path:
        """Generate static portal files including index.html, apps.json, assets, and QR codes."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        qr_dir = self.output_dir / "qr"
        qr_dir.mkdir(parents=True, exist_ok=True)
        assets_dest = self.output_dir / "assets"
        assets_dest.mkdir(parents=True, exist_ok=True)

        # 1. Copy web template assets
        if (self.web_template_dir / "assets").exists():
            shutil.copytree(self.web_template_dir / "assets", assets_dest, dirs_exist_ok=True)
        if (self.web_template_dir / "js").exists():
            js_dest = self.output_dir / "js"
            shutil.copytree(self.web_template_dir / "js", js_dest, dirs_exist_ok=True)

        # 2. Build apps list with QR codes and download links
        apps_data = []
        for meta in metadata_list:
            dl_url = f"https://github.com/{github_repo}/releases/download/{release_tag}/{meta.filename}"
            qr_file = qr_dir / f"{meta.filename}.png"
            self._generate_qr_code(dl_url, qr_file)

            item = meta.to_dict()
            item["download_url"] = dl_url
            item["qr_code_url"] = f"qr/{meta.filename}.png"
            item["size_mb"] = round(meta.size_bytes / (1024 * 1024), 2)
            apps_data.append(item)

        # 3. Write apps.json
        with open(self.output_dir / "apps.json", "w", encoding="utf-8") as f:
            json.dump(apps_data, f, indent=2)

        # 4. Copy or write index.html
        if (self.web_template_dir / "index.html").exists():
            shutil.copy2(self.web_template_dir / "index.html", self.output_dir / "index.html")

        log_success(f"Web Portal generated at {self.output_dir} with {len(apps_data)} applications.")
        return self.output_dir
