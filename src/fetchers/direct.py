"""
Direct URL and GitHub Release Asset Fetcher.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

from ..core.logger import log_error, log_info
from .base import BaseFetcher

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
        try:
            with self.session.get(source_url, stream=True, timeout=120) as stream_resp:
                stream_resp.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in stream_resp.iter_content(chunk_size=64 * 1024):
                        if chunk:
                            f.write(chunk)
            return True
        except Exception as e:
            log_error(f"Direct download failed: {e}")
            return False
