"""
Magisk, KernelSU, and APatch Root Module Packager.
"""

import os
import shutil
import zipfile
from pathlib import Path
from typing import Any, Dict, Optional

from ..core.logger import log_error, log_info, log_warn

class MagiskPackager:
    def __init__(self, template_dir: Optional[Path | str] = None):
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.template_dir = Path(template_dir) if template_dir else base_dir / "modules" / "template"

    def package_module(
        self,
        patched_apk: Path | str,
        stock_apk: Optional[Path | str],
        output_zip: Path | str,
        module_id: str,
        module_name: str,
        version_name: str,
        version_code: int,
        author: str = "RPDevs-Builds",
        description: str = "Patched application module",
        update_json_url: Optional[str] = None,
        arch: str = "arm64-v8a",
    ) -> bool:
        """Create flashable Magisk/KernelSU root module zip."""
        out = Path(output_zip)
        out.parent.mkdir(parents=True, exist_ok=True)
        apk_p = Path(patched_apk)

        if not apk_p.exists():
            log_error(f"Cannot package missing APK into module: {apk_p}")
            return False

        temp_dir = out.parent / f"mod_temp_{module_id}"
        shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 1. Copy template files if template dir exists
            if self.template_dir.exists():
                for item in self.template_dir.iterdir():
                    if item.is_dir():
                        shutil.copytree(item, temp_dir / item.name, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, temp_dir / item.name)

            # 2. Write module.prop
            module_prop_content = [
                f"id={module_id}",
                f"name={module_name}",
                f"version={version_name}",
                f"versionCode={version_code}",
                f"author={author}",
                f"description={description}",
            ]
            if update_json_url:
                module_prop_content.append(f"updateJson={update_json_url}")

            with open(temp_dir / "module.prop", "w", encoding="utf-8") as f:
                f.write("\n".join(module_prop_content) + "\n")

            # 3. Copy patched APK as base.apk
            shutil.copy2(apk_p, temp_dir / "base.apk")

            # 4. Copy stock APK if provided
            if stock_apk and Path(stock_apk).exists():
                stock_dir = temp_dir / "stock"
                stock_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(stock_apk, stock_dir / "base.apk")

            # 5. Create flashable zip
            log_info(f"Creating root module zip: {out.name}...")
            with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for file_p in temp_dir.rglob("*"):
                    if file_p.is_file():
                        arcname = file_p.relative_to(temp_dir)
                        z.write(file_p, arcname)

            shutil.rmtree(temp_dir, ignore_errors=True)
            log_info(f"Successfully created Magisk module: {out.name}")
            return True
        except Exception as e:
            log_error(f"Failed to create Magisk module: {e}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return False
