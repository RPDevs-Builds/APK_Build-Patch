"""
Configuration loader and schema validator.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from .logger import log_error, log_info

class ConfigLoader:
    def __init__(self, config_dir: Optional[Path | str] = None):
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path(__file__).resolve().parent.parent.parent / "config"

    def load_toml(self, filename: str) -> Dict[str, Any]:
        """Load a specific TOML configuration file."""
        filepath = self.config_dir / filename
        if not filepath.exists():
            log_error(f"Configuration file not found: {filepath}")
            return {}
        try:
            with open(filepath, "rb") as f:
                return tomllib.load(f)
        except Exception as e:
            log_error(f"Failed to parse {filename}: {e}")
            raise

    def get_patches_config(self) -> Dict[str, Any]:
        """Load and normalize patched apps configuration."""
        raw = self.load_toml("patches.toml")
        global_cfg = raw.get("global", {})
        apps = {}
        for key, val in raw.items():
            if key == "global" or not isinstance(val, dict):
                continue
            # Merge globals into app definition
            app_cfg = {**global_cfg, **val}
            app_cfg["table_name"] = key
            apps[key] = app_cfg
        return {"global": global_cfg, "apps": apps}

    def get_repos_config(self) -> Dict[str, Any]:
        """Load and normalize open source repositories configuration."""
        raw = self.load_toml("repos.toml")
        global_cfg = raw.get("global", {})
        repos = {}
        for key, val in raw.items():
            if key == "global" or not isinstance(val, dict):
                continue
            repo_cfg = {**global_cfg, **val}
            repo_cfg["name"] = key
            repos[key] = repo_cfg
        return {"global": global_cfg, "repos": repos}

    def get_sources_config(self) -> Dict[str, Any]:
        """Load sources configuration."""
        return self.load_toml("sources.toml")

    def get_storage_config(self) -> Dict[str, Any]:
        """Load storage and distribution configuration."""
        return self.load_toml("storage.toml")

def load_config(config_dir: Optional[Path | str] = None) -> ConfigLoader:
    return ConfigLoader(config_dir)
