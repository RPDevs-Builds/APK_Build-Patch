"""
Unit tests for Fetcher Subsystems.
"""

from unittest.mock import MagicMock, patch
from src.fetchers.apkmirror import APKMirrorFetcher
from src.fetchers.direct import DirectFetcher
from src.fetchers.archive import ArchiveFetcher

def test_apkmirror_fetcher_init():
    fetcher = APKMirrorFetcher({"request_timeout_seconds": 15})
    assert fetcher.timeout == 15
    assert "Mozilla" in fetcher.session.headers["User-Agent"]

def test_direct_fetcher(tmp_path):
    fetcher = DirectFetcher()
    test_file = tmp_path / "mock.apk"
    
    mock_resp = MagicMock()
    mock_resp.iter_content.return_value = [b"MOCK_APK_BYTES"]
    mock_resp.__enter__.return_value = mock_resp
    
    with patch.object(fetcher.session, "get", return_value=mock_resp):
        success = fetcher.download_apk("https://example.com/mock.apk", dest_path=test_file)
        assert success is True
        assert test_file.exists()
        assert test_file.read_bytes() == b"MOCK_APK_BYTES"

def test_archive_fetcher_parse():
    fetcher = ArchiveFetcher()
    mock_html = '<a href="com.google.android.youtube-19.16.39-all.apk">com.google.android.youtube-19.16.39-all.apk</a>'
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = mock_html
    
    with patch.object(fetcher.session, "get", return_value=mock_resp):
        vers = fetcher.get_latest_versions("https://archive.org/download/apks")
        assert "19.16.39" in vers
