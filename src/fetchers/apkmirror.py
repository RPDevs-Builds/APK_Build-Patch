"""
APKMirror Scraper and Downloader Subsystem.
"""

import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests
from bs4 import BeautifulSoup

from ..core.logger import log_error, log_info, log_warn
from .base import BaseFetcher

class APKMirrorFetcher(BaseFetcher):
    BASE_URL = "https://www.apkmirror.com"
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:148.0) Gecko/20100101 Firefox/148.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "DNT": "1",
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        self.timeout = self.config.get("request_timeout_seconds", 30)

    def _get(self, url: str) -> requests.Response:
        full_url = url if url.startswith("http") else f"{self.BASE_URL}{url}"
        retries = self.config.get("max_retries", 3)
        delay = self.config.get("retry_delay_seconds", 2)
        for attempt in range(1, retries + 1):
            try:
                resp = self.session.get(full_url, timeout=self.timeout)
                if resp.status_code == 200:
                    return resp
                log_warn(f"APKMirror GET {full_url} returned HTTP {resp.status_code} (attempt {attempt}/{retries})")
            except Exception as e:
                log_warn(f"APKMirror GET error on {full_url}: {e} (attempt {attempt}/{retries})")
            time.sleep(delay * attempt)
        raise RuntimeError(f"Failed to fetch {full_url} from APKMirror after {retries} attempts.")

    def get_latest_versions(self, source_url: str) -> List[str]:
        """Scrape version list from an APKMirror app page or category."""
        clean_url = source_url.rstrip("/")
        resp = self._get(clean_url)
        soup = BeautifulSoup(resp.text, "html.parser")
        versions = []

        for row in soup.select("div.table-row.headerFont, div.appRow"):
            text = row.get_text()
            match = re.search(r"(\d+\.\d+(?:\.\d+)?(?:\.\d+)?)", text)
            if match:
                ver = match.group(1)
                # Filter out betas and alphas if standard release requested
                if "beta" not in text.lower() and "alpha" not in text.lower():
                    if ver not in versions:
                        versions.append(ver)

        if not versions:
            # Fallback regex on whole page
            matches = re.findall(r"Version:\s*</span>\s*<span[^>]*>([0-9\.]+)", resp.text)
            for m in matches:
                if m not in versions:
                    versions.append(m)

        return versions

    def download_apk(
        self,
        source_url: str,
        version: str,
        dest_path: Path | str,
        arch: str = "all",
        dpi: str = "nodpi",
    ) -> bool:
        """Locate variant, resolve download token links, and download APK or bundle."""
        dest = Path(dest_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        norm_ver = version.replace(" ", "-").replace(".", "-")
        app_slug = source_url.rstrip("/").split("/")[-1]
        
        # 1. Fetch release variants table
        release_url = f"{source_url.rstrip('/')}/{app_slug}-{norm_ver}-release/"
        log_info(f"Checking APKMirror release page: {release_url}")
        
        try:
            resp = self._get(release_url)
        except Exception:
            # Try alternate URL without app_slug repetition
            release_url = f"{source_url.rstrip('/')}/{norm_ver}-release/"
            resp = self._get(release_url)

        soup = BeautifulSoup(resp.text, "html.parser")
        download_url = None
        is_bundle = False

        app_archs = ["universal", "noarch", "arm64-v8a + armeabi-v7a"]
        if arch != "all":
            norm_arch = "armeabi-v7a" if arch == "arm-v7a" else arch
            app_archs.append(norm_arch)

        app_dpis = ["nodpi", "anydpi"]
        if dpi:
            app_dpis.append(dpi)

        # Parse variants table
        rows = soup.select("div.table-row.headerFont")
        for row in rows:
            cells = [c.get_text(strip=True) for c in row.select("div.table-cell, div")]
            if len(cells) < 4:
                continue
            
            row_text = " ".join(cells).lower()
            link_tag = row.select_one("a.accent_color, a[href*='download/']")
            if not link_tag:
                continue
            
            # Check architecture & dpi match
            arch_match = any(a in row_text for a in app_archs)
            dpi_match = any(d in row_text for d in app_dpis) or "nodpi" in row_text
            
            if arch_match and dpi_match:
                download_url = link_tag.get("href")
                if "bundle" in row_text or "apkm" in row_text:
                    is_bundle = True
                break

        # Fallback to first available download button if specific variant parsing didn't match
        if not download_url:
            first_btn = soup.select_one("a.downloadButton, a[href*='download/']")
            if first_btn:
                download_url = first_btn.get("href")

        if not download_url:
            log_error(f"Could not find valid download variant on APKMirror for {version} ({arch})")
            return False

        # 2. Navigate to intermediate download page
        log_info(f"Navigating to download page: {download_url}")
        int_resp = self._get(download_url)
        int_soup = BeautifulSoup(int_resp.text, "html.parser")
        
        # 3. Find final download button
        final_link_tag = int_soup.select_one("a.btn[href*='download.php'], span > a[rel='nofollow']")
        if not final_link_tag or not final_link_tag.get("href"):
            # Check for alternative button
            final_link_tag = int_soup.select_one("a[href*='key=']")
            
        if not final_link_tag:
            log_error("Could not extract final download link from APKMirror intermediate page.")
            return False

        direct_download_url = final_link_tag.get("href")
        if not direct_download_url.startswith("http"):
            direct_download_url = f"{self.BASE_URL}{direct_download_url}"

        # 4. Stream download to target file
        out_file = dest.with_suffix(".apkm") if is_bundle else dest
        log_info(f"Downloading stream to {out_file} from {direct_download_url}...")
        
        with self.session.get(direct_download_url, stream=True, timeout=120) as stream_resp:
            stream_resp.raise_for_status()
            with open(out_file, "wb") as f:
                for chunk in stream_resp.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        f.write(chunk)

        log_info(f"Successfully fetched {out_file} ({out_file.stat().st_size / (1024 * 1024):.2f} MB)")
        return True
