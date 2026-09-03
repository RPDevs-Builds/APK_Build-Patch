"""
Split APK Bundle Merger Subsystem.
Integrates APKEditor.jar to merge split APK bundles (.apkm, .xapk, .apks) into standalone APKs.
"""

import shutil
from pathlib import Path
from typing import Optional
import requests

from ..core.logger import log_error, log_info, log_warn
from ..core.utils import find_java, run_cmd
from .signer import APKSigner

class SplitMerger:
    def __init__(self, apkeditor_jar: Optional[Path | str] = None):
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.apkeditor_jar = Path(apkeditor_jar) if apkeditor_jar else base_dir / "bin" / "apkeditor.jar"
        self.java_bin = find_java("21")
        self.signer = APKSigner()

    def _ensure_apkeditor(self) -> bool:
        if self.apkeditor_jar.exists():
            return True
        self.apkeditor_jar.parent.mkdir(parents=True, exist_ok=True)
        url = "https://github.com/REAndroid/APKEditor/releases/download/V1.4.7/APKEditor-1.4.7.jar"
        log_info(f"Downloading APKEditor from {url}...")
        try:
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            with open(self.apkeditor_jar, "wb") as f:
                f.write(resp.content)
            return True
        except Exception as e:
            log_error(f"Failed to fetch APKEditor: {e}")
            return False

    def merge_bundle(self, bundle_path: Path | str, output_apk_path: Path | str) -> bool:
        """Merge a split APK bundle into a standalone signed APK."""
        inp = Path(bundle_path)
        out = Path(output_apk_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        if not self._ensure_apkeditor():
            return False

        unsigned_out = out.parent / f"{out.stem}-unsigned.apk"

        log_info(f"Merging split APK bundle: {inp.name} -> {out.name}...")
        cmd = [
            self.java_bin,
            "-jar",
            str(self.apkeditor_jar),
            "merge",
            "-i",
            str(inp),
            "-o",
            str(unsigned_out),
            "-clean-meta",
            "-f",
        ]

        try:
            run_cmd(cmd, check=True)
            # Sign merged standalone APK
            success = self.signer.sign_apk(unsigned_out, out)
            if unsigned_out.exists():
                unsigned_out.unlink()
            return success
        except Exception as e:
            log_error(f"Split APK merge failed: {e}")
            if unsigned_out.exists():
                unsigned_out.unlink()
            return False
