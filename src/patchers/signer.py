"""
APK Signer & Zipalign Subsystem.
Wraps apksigner.jar and manages keystores.
"""

import os
import shutil
from pathlib import Path
from typing import Optional

from ..core.logger import log_error, log_info, log_warn
from ..core.utils import find_java, run_cmd

class APKSigner:
    def __init__(
        self,
        keystore_path: Optional[Path | str] = None,
        keystore_pass: str = "pass:123456789",
        key_alias: str = "jhc",
        key_pass: str = "pass:123456789",
        apksigner_jar: Optional[Path | str] = None,
    ):
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.keystore_path = Path(keystore_path) if keystore_path else base_dir / "bin" / "keystores" / "ks-p12.keystore"
        if not self.keystore_path.exists():
            # Fallback to ks.keystore
            alt = base_dir / "bin" / "keystores" / "ks.keystore"
            if alt.exists():
                self.keystore_path = alt

        self.keystore_pass = os.environ.get("KEYSTORE_PASSWORD", keystore_pass)
        self.key_alias = os.environ.get("KEY_ALIAS", key_alias)
        self.key_pass = os.environ.get("KEY_PASSWORD", key_pass)
        self.apksigner_jar = Path(apksigner_jar) if apksigner_jar else base_dir / "bin" / "apksigner.jar"
        self.java_bin = find_java("21")

    def sign_apk(self, input_apk: Path | str, output_apk: Optional[Path | str] = None) -> bool:
        """Sign the APK using apksigner.jar with V1-V4 signature support."""
        inp = Path(input_apk)
        out = Path(output_apk) if output_apk else inp
        
        if not inp.exists():
            log_error(f"Cannot sign missing APK: {inp}")
            return False

        if not self.apksigner_jar.exists():
            log_error(f"apksigner.jar not found at {self.apksigner_jar}")
            return False

        # Clean old idsig if present
        idsig = inp.with_suffix(".apk.idsig")
        if idsig.exists():
            idsig.unlink()

        cmd = [
            self.java_bin,
            "-jar",
            str(self.apksigner_jar),
            "sign",
            "--ks",
            str(self.keystore_path),
            "--ks-pass",
            self.keystore_pass,
            "--key-pass",
            self.key_pass,
            "--ks-key-alias",
            self.key_alias,
            "--out",
            str(out),
            str(inp),
        ]

        log_info(f"Signing {inp.name} -> {out.name}...")
        try:
            res = run_cmd(cmd, check=True)
            log_info(f"Successfully signed {out.name}")
            return True
        except Exception as e:
            log_error(f"Failed to sign APK: {e}")
            return False

    def verify_signature(self, apk_path: Path | str) -> bool:
        """Verify APK signature and return True if valid."""
        cmd = [
            self.java_bin,
            "-jar",
            str(self.apksigner_jar),
            "verify",
            "--print-certs",
            str(apk_path),
        ]
        try:
            res = run_cmd(cmd, check=False)
            return res.returncode == 0
        except Exception:
            return False
