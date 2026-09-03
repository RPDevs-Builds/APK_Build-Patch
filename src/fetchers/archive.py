"""
Archive.org & Direct HTTP / GitHub Releases Fetchers.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests
from bs4 import BeautifulSoup

from ..core.logger import log_error, log_info, log_warn
from .base import BaseFetcher

class ArchiveFetcher(BaseFetcher):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "RPDevs-APK-Engine/1.0"})
        self.timeout = self.config.get("timeout_seconds", 45)

    def get_latest_versions(self, source_url: str) -> List[str]:
        resp = self.session.get(source_url, timeout=self.timeout)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        versions = []
        for a in soup.select("a[href]"):
            href = a.get("href")
            match = re.search(r"-(\d+\.\d+(?:\.\d+)?)-", href)
            if match:
                v = match.group(1)
                if v not in versions:
                    versions.append(v)
        return versions

    def download_apk(
        self,
        source_url: str,
        version: str,
        dest_path: Path | str,
        arch: str = "all",
        dpi: str = "nodpi",
    ) -> bool:
        dest = Path(dest_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        resp = self.session.get(source_url, timeout=self.timeout)
        if resp.status_code != 200:
            return False

        soup = BeautifulSoup(resp.text, "html.parser")
        target_file = None
        norm_ver = version.replace(" ", "").lstrip("v")
        arch_norm = "arm64-v8a" if arch == "arm64-v8a" else "all"

        for a in soup.select("a[href]"):
            href = a.get("href")
            if norm_ver in href and (arch_norm in href or "all" in href or ".apk" in href):
                target_file = href
                break

        if not target_file:
            log_error(f"File not found in Archive.org directory for version {version}")
            return False

        file_url = f"{source_url.rstrip('/')}/{target_file.lstrip('/')}"
        log_info(f"Downloading from Archive.org: {file_url}")
        
        with self.session.get(file_url, stream=True, timeout=120) as stream_resp:
            stream_resp.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in stream_resp.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        f.write(chunk)
        return True


class DirectFetcher(BaseFetcher):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "RPDevs-APK-Engine/1.0"})

    def get_latest_versions(self, source_url: str) -> List[str]:
        return ["direct"]

    def download_apk(
        self,
        source_url: str,
        version: str = "direct",
        dest_path: Path | str = "temp/direct.apk",
        arch: str = "all",
        dpi: str = "nodpi",
    ) -> bool:
        dest = Path(dest_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        log_info(f"Downloading direct URL: {source_url}")
        
        with self.session.get(source_url, stream=True, timeout=120) as stream_resp:
            stream_resp.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in stream_resp.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        f.write(chunk)
        return True
