"""
Unit tests for metadata extraction and generator classes.
"""

import zipfile
from pathlib import Path
from src.storage.apk_metadata import APKMetadataExtractor, APKMetadata

def test_metadata_extraction_zip(tmp_path):
    mock_apk = tmp_path / "com.example.app-1.0.0.apk"
    with zipfile.ZipFile(mock_apk, "w") as z:
        z.writestr("AndroidManifest.xml", b"mock_manifest")
        z.writestr("lib/arm64-v8a/libtest.so", b"mock_lib")

    extractor = APKMetadataExtractor()
    meta = extractor.extract_metadata(mock_apk)
    
    assert meta.filename == "com.example.app-1.0.0.apk"
    assert "arm64-v8a" in meta.architectures
    assert meta.sha256 != ""
    assert meta.size_bytes > 0
