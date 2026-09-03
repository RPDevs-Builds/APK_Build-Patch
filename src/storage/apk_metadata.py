"""
APK Metadata & Icon Extractor.
Extracts package name, version, min SDK, permissions, architecture, and icons from built APKs.
"""

import os
import re
import shutil
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.logger import log_error, log_info, log_warn
from ..core.utils import calculate_md5, calculate_sha256, run_cmd

@dataclass
class APKMetadata:
    filename: str
    filepath: str
    package_name: str
    version_name: str
    version_code: int
    app_name: str
    min_sdk: int
    target_sdk: int
    architectures: List[str]
    size_bytes: int
    sha256: str
    md5: str
    icon_path: Optional[str] = None
    category: str = "General"
    description: str = ""
    is_module: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class APKMetadataExtractor:
    def __init__(self, aapt2_binary: Optional[Path | str] = None):
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.aapt2_binary = None
        if aapt2_binary and Path(aapt2_binary).exists():
            self.aapt2_binary = str(aapt2_binary)
        elif shutil.which("aapt2"):
            self.aapt2_binary = shutil.which("aapt2")
        else:
            # Check local bin/aapt2/
            arch = "x86_64"
            local_aapt2 = base_dir / "bin" / "aapt2" / f"aapt2-{arch}"
            if local_aapt2.exists():
                local_aapt2.chmod(0o755)
                self.aapt2_binary = str(local_aapt2)

    def extract_metadata(
        self,
        apk_path: Path | str,
        icons_output_dir: Optional[Path | str] = None,
        default_category: str = "General",
        default_description: str = "",
    ) -> APKMetadata:
        """Parse APK metadata and optionally extract the application icon."""
        p = Path(apk_path)
        if not p.exists():
            raise FileNotFoundError(f"APK file not found: {p}")

        size_bytes = p.stat().st_size
        sha256 = calculate_sha256(p)
        md5 = calculate_md5(p)

        # Defaults based on filename
        pkg_name = "unknown.package"
        ver_name = "1.0.0"
        ver_code = 1
        app_name = p.stem.replace("-", " ").title()
        min_sdk = 26
        target_sdk = 34
        archs = ["universal"]
        icon_rel_path = None

        if p.name.endswith(".zip"):
            # Magisk module
            return APKMetadata(
                filename=p.name,
                filepath=str(p),
                package_name=f"module.{p.stem}",
                version_name=ver_name,
                version_code=ver_code,
                app_name=f"{app_name} (Root Module)",
                min_sdk=min_sdk,
                target_sdk=target_sdk,
                architectures=["arm64-v8a"],
                size_bytes=size_bytes,
                sha256=sha256,
                md5=md5,
                icon_path=None,
                category="Root Modules (Magisk/KSU)",
                description=default_description or "Root module for Magisk, KernelSU, and APatch",
                is_module=True,
            )

        # Try aapt2 dump badging if available
        if self.aapt2_binary:
            try:
                res = run_cmd([self.aapt2_binary, "dump", "badging", str(p)], check=False)
                if res.returncode == 0 and res.stdout:
                    out = res.stdout
                    
                    # package: name='com.google.android.youtube' versionCode='1533502208' versionName='19.16.39'
                    pkg_match = re.search(r"package:\s*name='([^']+)'\s*versionCode='([^']+)'\s*versionName='([^']*)'", out)
                    if pkg_match:
                        pkg_name = pkg_match.group(1)
                        try:
                            ver_code = int(pkg_match.group(2))
                        except ValueError:
                            ver_code = 1
                        ver_name = pkg_match.group(3) or ver_name

                    # application-label:'YouTube'
                    label_match = re.search(r"application-label(?:-[a-zA-Z_-]+)?:\s*'([^']+)'", out)
                    if label_match:
                        app_name = label_match.group(1)

                    # sdkVersion:'26'
                    sdk_match = re.search(r"sdkVersion:\s*'(\d+)'", out)
                    if sdk_match:
                        min_sdk = int(sdk_match.group(1))

                    # targetSdkVersion:'34'
                    target_match = re.search(r"targetSdkVersion:\s*'(\d+)'", out)
                    if target_match:
                        target_sdk = int(target_match.group(1))

                    # native-code: 'arm64-v8a' 'armeabi-v7a'
                    native_match = re.search(r"native-code:\s*(.+)", out)
                    if native_match:
                        archs = [a.strip("'\"") for a in native_match.group(1).split()]

                    # application-icon-xxxhdpi:'res/drawable-xxxhdpi/icon.png'
                    icon_match = re.search(r"application-icon(?:-[^:]+)?:\s*'([^']+)'", out)
                    if icon_match and icons_output_dir:
                        icon_res_path = icon_match.group(1)
                        icon_dest_dir = Path(icons_output_dir)
                        icon_dest_dir.mkdir(parents=True, exist_ok=True)
                        dest_icon = icon_dest_dir / f"{pkg_name}.png"
                        
                        try:
                            with zipfile.ZipFile(p, "r") as z:
                                if icon_res_path in z.namelist():
                                    with open(dest_icon, "wb") as f_icon:
                                        f_icon.write(z.read(icon_res_path))
                                    icon_rel_path = str(dest_icon.name)
                        except Exception as e:
                            log_warn(f"Could not extract icon from APK: {e}")
            except Exception as e:
                log_warn(f"aapt2 metadata dump failed: {e}")

        # If aapt2 was unavailable or didn't extract architecture, check lib/ inside zip
        if archs == ["universal"]:
            try:
                with zipfile.ZipFile(p, "r") as z:
                    names = z.namelist()
                    detected = set()
                    for n in names:
                        if n.startswith("lib/arm64-v8a/"):
                            detected.add("arm64-v8a")
                        elif n.startswith("lib/armeabi-v7a/"):
                            detected.add("arm-v7a")
                        elif n.startswith("lib/x86_64/"):
                            detected.add("x86_64")
                        elif n.startswith("lib/x86/"):
                            detected.add("x86")
                    if detected:
                        archs = sorted(list(detected))
            except Exception:
                pass

        return APKMetadata(
            filename=p.name,
            filepath=str(p),
            package_name=pkg_name,
            version_name=ver_name,
            version_code=ver_code,
            app_name=app_name,
            min_sdk=min_sdk,
            target_sdk=target_sdk,
            architectures=archs,
            size_bytes=size_bytes,
            sha256=sha256,
            md5=md5,
            icon_path=icon_rel_path,
            category=default_category,
            description=default_description,
            is_module=False,
        )
