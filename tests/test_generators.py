"""
Unit tests for F-Droid, Obtainium, Web Portal, and Magisk OTA generators.
"""

import json
from pathlib import Path
from src.storage.apk_metadata import APKMetadata
from src.storage.fdroid_generator import FDroidGenerator
from src.storage.obtainium_generator import ObtainiumGenerator
from src.storage.web_portal_generator import WebPortalGenerator
from src.storage.magisk_update_generator import MagiskUpdateGenerator

def sample_metadata(tmp_path):
    mock_file = tmp_path / "YouTube-ReVanced-arm64.apk"
    mock_file.write_bytes(b"TEST_APK_CONTENT")
    return APKMetadata(
        filename="YouTube-ReVanced-arm64.apk",
        filepath=str(mock_file),
        package_name="com.google.android.youtube",
        version_name="19.16.39",
        version_code=1533502208,
        app_name="YouTube ReVanced",
        min_sdk=26,
        target_sdk=34,
        architectures=["arm64-v8a"],
        size_bytes=len(b"TEST_APK_CONTENT"),
        sha256="abc123sha256",
        md5="abc123md5",
        category="Patched - ReVanced",
        description="Patched YouTube",
    )

def test_fdroid_generator(tmp_path):
    meta = sample_metadata(tmp_path)
    gen = FDroidGenerator({"output_dir": str(tmp_path / "fdroid")})
    out_dir = gen.generate_repository([meta])
    
    assert (out_dir / "repo" / "index-v1.json").exists()
    assert (out_dir / "repo" / "index-v1.jar").exists()
    assert (out_dir / "repo" / "index-v2.json").exists()

    with open(out_dir / "repo" / "index-v1.json") as f:
        data = json.load(f)
        assert len(data["apps"]) == 1
        assert data["apps"][0]["packageName"] == "com.google.android.youtube"

def test_obtainium_generator(tmp_path):
    meta = sample_metadata(tmp_path)
    out_file = tmp_path / "obtainium-feed.json"
    gen = ObtainiumGenerator({"output_file": str(out_file)})
    gen.generate_feed([meta])

    assert out_file.exists()
    with open(out_file) as f:
        data = json.load(f)
        assert len(data["apps"]) == 1
        assert data["apps"][0]["id"] == "com.google.android.youtube"

def test_magisk_update_generator(tmp_path):
    meta = sample_metadata(tmp_path)
    meta.is_module = True
    meta.package_name = "module.youtube-revanced"
    
    gen = MagiskUpdateGenerator(output_dir=tmp_path / "modules_ota")
    files = gen.generate_update_jsons([meta])
    
    assert len(files) == 1
    assert files[0].name == "youtube-revanced-update.json"
    with open(files[0]) as f:
        data = json.load(f)
        assert data["version"] == "19.16.39"
