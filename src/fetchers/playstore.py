"""
Google Play Store Downloader Subsystem.
Supports gplaycli, apkeep, and token dispensation.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.logger import log_error, log_info, log_warn
from ..core.utils import run_cmd
from .base import BaseFetcher

class PlayStoreFetcher(BaseFetcher):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.backend = self.config.get("backend", "auto")
        self.device_codename = self.config.get("device_codename", "bramble")
        self.email = os.environ.get("GPLAY_EMAIL")
        self.token = os.environ.get("GPLAY_TOKEN") or os.environ.get("GPLAY_PASSWORD")

    def _has_gplaycli(self) -> bool:
        return shutil.which("gplaycli") is not None

    def _get_apkeep_bin(self) -> Optional[str]:
        base_dir = Path(__file__).resolve().parent.parent.parent
        local_bin = base_dir / "bin" / "apkeep"
        if local_bin.exists():
            local_bin.chmod(0o755)
            return str(local_bin)
        return shutil.which("apkeep")

    def _has_apkeep(self) -> bool:
        return self._get_apkeep_bin() is not None

    def get_latest_versions(self, pkg_name: str) -> List[str]:
        """Query versions available for package."""
        apkeep_bin = self._get_apkeep_bin()
        if apkeep_bin:
            try:
                # apkeep -l -a pkg temp/
                res = run_cmd([apkeep_bin, "-l", "-a", pkg_name, "temp/"], check=False)
                if res.returncode == 0 and res.stdout:
                    import re
                    vers = re.findall(r"(\d+\.\d+(?:\.\d+)?(?:\.\d+)?)", res.stdout)
                    if vers:
                        return vers[::-1] # Reverse to have latest first
            except Exception:
                pass
        return ["latest"]

    def download_apk(
        self,
        pkg_name: str,
        version: str = "latest",
        dest_path: Path | str = "temp/stock.apk",
        arch: str = "all",
        dpi: str = "nodpi",
    ) -> bool:
        """Download APK from Google Play / APKPure via apkeep or gplaycli."""
        dest = Path(dest_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        # Mode 1: apkeep (Rust-based high speed downloader with version pinning support)
        apkeep_bin = self._get_apkeep_bin()
        if (self.backend in ("auto", "apkeep")) and apkeep_bin:
            log_info(f"Downloading {pkg_name} ({version}) via apkeep...")
            out_dir = dest.parent / f"apkeep_{pkg_name.replace('.', '_')}"
            out_dir.mkdir(parents=True, exist_ok=True)
            
            target_arg = f"{pkg_name}@{version}" if version and version not in ("auto", "latest") else pkg_name
            cmd = [apkeep_bin, "-a", target_arg, str(out_dir)]
            
            try:
                res = run_cmd(cmd, check=True)
                # Find downloaded apk or apks
                apks = list(out_dir.glob("*.apk")) + list(out_dir.glob("*.apkm")) + list(out_dir.glob("*.xapk"))
                if apks:
                    found_file = apks[0]
                    target_dest = dest.with_suffix(found_file.suffix)
                    shutil.move(str(found_file), str(target_dest))
                    shutil.rmtree(out_dir, ignore_errors=True)
                    log_info(f"Successfully downloaded {pkg_name} via apkeep to {target_dest}")
                    return True
            except Exception as e:
                log_warn(f"apkeep download failed for {pkg_name}: {e}")
                shutil.rmtree(out_dir, ignore_errors=True)

        # Mode 2: gplaycli (Python Google Play CLI client)
        if (self.backend in ("auto", "gplaycli")) and self._has_gplaycli():
            log_info(f"Downloading {pkg_name} via gplaycli...")
            out_dir = dest.parent / f"gplay_{pkg_name}"
            out_dir.mkdir(parents=True, exist_ok=True)
            cmd = ["gplaycli", "-d", "-p", pkg_name, "-f", str(out_dir)]
            if self.email and self.token:
                cmd.extend(["-u", self.email, "-p", self.token])
            try:
                res = run_cmd(cmd, check=True)
                apks = list(out_dir.glob("*.apk")) + list(out_dir.glob("*.apks"))
                if apks:
                    shutil.move(str(apks[0]), str(dest))
                    shutil.rmtree(out_dir, ignore_errors=True)
                    log_info(f"Successfully downloaded {pkg_name} via gplaycli to {dest}")
                    return True
            except Exception as e:
                log_warn(f"gplaycli download failed for {pkg_name}: {e}")
                shutil.rmtree(out_dir, ignore_errors=True)

        log_error(f"PlayStoreFetcher could not download {pkg_name}. Ensure 'apkeep' or 'gplaycli' is installed or use APKMirror fallback.")
        return False
