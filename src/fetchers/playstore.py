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

    def _has_apkeep(self) -> bool:
        return shutil.which("apkeep") is not None

    def get_latest_versions(self, pkg_name: str) -> List[str]:
        """Query Google Play Store for latest version code/name."""
        if self._has_gplaycli() and (self.email or self.config.get("token_dispenser_url")):
            try:
                cmd = ["gplaycli", "-d", "-p", pkg_name, "--version"]
                res = run_cmd(cmd, check=False)
                if res.returncode == 0 and res.stdout:
                    return [res.stdout.strip()]
            except Exception as e:
                log_warn(f"gplaycli version check failed: {e}")
        return ["latest"]

    def download_apk(
        self,
        pkg_name: str,
        version: str = "latest",
        dest_path: Path | str = "temp/stock.apk",
        arch: str = "all",
        dpi: str = "nodpi",
    ) -> bool:
        """Download APK from Google Play Store."""
        dest = Path(dest_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        # Mode 1: apkeep (Rust-based high speed downloader with anonymous token support)
        if (self.backend in ("auto", "apkeep")) and self._has_apkeep():
            log_info(f"Downloading {pkg_name} via apkeep...")
            out_dir = dest.parent / f"apkeep_{pkg_name}"
            out_dir.mkdir(parents=True, exist_ok=True)
            cmd = ["apkeep", "-a", pkg_name, str(out_dir)]
            try:
                res = run_cmd(cmd, check=True)
                # Find downloaded apk or apks
                apks = list(out_dir.glob("*.apk")) + list(out_dir.glob("*.apkm")) + list(out_dir.glob("*.xapk"))
                if apks:
                    shutil.move(str(apks[0]), str(dest))
                    shutil.rmtree(out_dir, ignore_errors=True)
                    log_info(f"Successfully downloaded {pkg_name} via apkeep to {dest}")
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
