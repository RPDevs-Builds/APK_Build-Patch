"""
Process execution, hashing, semver comparison, and filesystem helpers.
"""

import hashlib
import os
import re
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

from .logger import log_error, log_info, log_warn

def run_cmd(
    cmd: List[str] | str,
    cwd: Optional[Path | str] = None,
    env: Optional[Dict[str, str]] = None,
    check: bool = True,
    capture_output: bool = True,
) -> subprocess.CompletedProcess:
    """Run a shell command with proper error reporting and environment."""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)

    shell = isinstance(cmd, str)
    try:
        res = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            env=full_env,
            shell=shell,
            text=True,
            check=check,
            capture_output=capture_output,
        )
        return res
    except subprocess.CalledProcessError as e:
        log_error(f"Command failed with exit code {e.returncode}: {cmd}")
        if e.stdout:
            log_warn(f"STDOUT: {e.stdout.strip()}")
        if e.stderr:
            log_error(f"STDERR: {e.stderr.strip()}")
        raise

def calculate_sha256(filepath: Path | str) -> str:
    """Calculate the SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192 * 16):
            sha256.update(chunk)
    return sha256.hexdigest()

def calculate_md5(filepath: Path | str) -> str:
    """Calculate the MD5 hash of a file."""
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192 * 16):
            md5.update(chunk)
    return md5.hexdigest()

def extract_zip(zip_path: Path | str, dest_dir: Path | str) -> None:
    """Safely extract a zip or apk file to target directory."""
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(dest)

def parse_semver(version_str: str) -> Tuple[int, ...]:
    """Parse version string like 'v2.1.0' or '21.07.34' into a comparable tuple."""
    clean_ver = re.sub(r"^[^\d]*", "", version_str)
    parts = re.split(r"[.\-_]", clean_ver)
    num_parts = []
    for p in parts:
        nums = re.findall(r"\d+", p)
        if nums:
            num_parts.append(int(nums[0]))
        else:
            num_parts.append(0)
    return tuple(num_parts) if num_parts else (0,)

def compare_versions(ver1: str, ver2: str) -> int:
    """Compare two version strings (-1 if ver1 < ver2, 0 if equal, 1 if ver1 > ver2)."""
    p1 = parse_semver(ver1)
    p2 = parse_semver(ver2)
    max_len = max(len(p1), len(p2))
    p1_padded = p1 + (0,) * (max_len - len(p1))
    p2_padded = p2 + (0,) * (max_len - len(p2))
    if p1_padded < p2_padded:
        return -1
    elif p1_padded > p2_padded:
        return 1
    return 0

def find_java(preferred_version: str = "21") -> str:
    """Locate java binary or verify available JAVA_HOME."""
    env_var_name = f"JAVA_HOME_{preferred_version}_X64"
    if env_var_name in os.environ and os.path.exists(os.path.join(os.environ[env_var_name], "bin", "java")):
        return os.path.join(os.environ[env_var_name], "bin", "java")
    if "JAVA_HOME" in os.environ and os.path.exists(os.path.join(os.environ["JAVA_HOME"], "bin", "java")):
        return os.path.join(os.environ["JAVA_HOME"], "bin", "java")
    return shutil.which("java") or "java"
