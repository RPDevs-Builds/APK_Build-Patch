"""
Unit tests for configuration loaders and schemas.
"""

from pathlib import Path
from src.core.config_loader import load_config

def test_load_patches_config():
    loader = load_config()
    cfg = loader.get_patches_config()
    assert "global" in cfg
    assert "apps" in cfg
    assert "YouTube" in cfg["apps"]
    assert cfg["apps"]["YouTube"]["pkg_name"] == "com.google.android.youtube"
    assert cfg["apps"]["YouTube"]["enabled"] is True

def test_load_repos_config():
    loader = load_config()
    cfg = loader.get_repos_config()
    assert "global" in cfg
    assert "repos" in cfg
    assert "NewPipe" in cfg["repos"]
    assert cfg["repos"]["NewPipe"]["build_system"] == "gradle"
    assert "RPDev-Launcher" in cfg["repos"]

def test_load_sources_config():
    loader = load_config()
    cfg = loader.get_sources_config()
    assert "priorities" in cfg
    assert "order" in cfg["priorities"]
    assert "apkmirror" in cfg["priorities"]["order"]
    assert "playstore" in cfg

def test_load_storage_config():
    loader = load_config()
    cfg = loader.get_storage_config()
    assert "fdroid" in cfg
    assert "obtainium" in cfg
    assert "web_portal" in cfg
    assert cfg["fdroid"]["enabled"] is True
