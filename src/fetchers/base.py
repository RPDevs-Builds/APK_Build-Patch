"""
Base abstract class for all APK fetchers.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

class BaseFetcher(ABC):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    @abstractmethod
    def get_latest_versions(self, source_url_or_pkg: str) -> List[str]:
        """Fetch available release versions for the specified target."""
        pass

    @abstractmethod
    def download_apk(
        self,
        source_url_or_pkg: str,
        version: str,
        dest_path: Path | str,
        arch: str = "all",
        dpi: str = "nodpi",
    ) -> bool:
        """Download APK or bundle matching version/arch/dpi to dest_path."""
        pass
