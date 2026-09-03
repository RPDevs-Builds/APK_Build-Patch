"""
Uptodown Scraper & Downloader Subsystem.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests
from bs4 import BeautifulSoup

from ..core.logger import log_error, log_info, log_warn
from .base import BaseFetcher

class UptodownFetcher(BaseFetcher):
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:148.0) Gecko/20100101 Firefox/148.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        self.timeout = self.config.get("timeout_seconds", 30)

    def get_latest_versions(self, source_url: str) -> List[str]:
        clean_url = source_url.rstrip("/")
        versions_url = f"{clean_url}/versions"
        resp = self.session.get(versions_url, timeout=self.timeout)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        versions = []
        for el in soup.select("span.version, div.version"):
            v = el.get_text(strip=True)
            if v and v not in versions:
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
        download_page = f"{source_url.rstrip('/')}/download"
        
        log_info(f"Navigating to Uptodown download page: {download_page}")
        resp = self.session.get(download_page, timeout=self.timeout)
        if resp.status_code != 200:
            return False

        soup = BeautifulSoup(resp.text, "html.parser")
        dl_btn = soup.select_one("button#detail-download-button, a#detail-download-button")
        if not dl_btn:
            log_error(f"Uptodown download button not found for {source_url}")
            return False

        data_url = dl_btn.get("data-url")
        if not data_url:
            data_url = dl_btn.get("href")

        if not data_url:
            return False

        if not data_url.startswith("http"):
            direct_url = f"https://dw.uptodown.com/dwn/{data_url}"
        else:
            direct_url = data_url

        log_info(f"Streaming from Uptodown: {direct_url}")
        with self.session.get(direct_url, stream=True, timeout=120) as stream_resp:
            stream_resp.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in stream_resp.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        f.write(chunk)

        return True
