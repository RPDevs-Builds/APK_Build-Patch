"""
Abstract BaseBuilder Class for Open-Source Android Repositories.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

class BaseBuilder(ABC):
    def __init__(self, workspace_dir: Path | str = "temp/build_workspace"):
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def build_from_source(
        self,
        repo_url: str,
        branch: str,
        output_dir: Path | str,
        config: Dict[str, Any],
    ) -> List[Path]:
        """Clone and compile Android project, returning list of built APK paths."""
        pass
