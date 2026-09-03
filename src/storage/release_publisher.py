"""
Release Publisher & Webhook Notification Broadcaster.
Publishes GitHub Releases, prunes legacy builds, and alerts Telegram/Discord channels.
"""

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

from ..core.logger import log_error, log_info, log_step, log_success, log_warn
from ..core.utils import run_cmd
from .apk_metadata import APKMetadata

class ReleasePublisher:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.github_repo = self.config.get("github_repository", "RPDevs-Builds/APK_Build-Patch")
        self.tag_prefix = self.config.get("tag_prefix", "v")
        self.keep_recent_count = self.config.get("keep_recent_releases_count", 10)

    def publish_github_release(
        self,
        tag: str,
        release_title: str,
        release_notes: str,
        assets: List[Path | str],
    ) -> bool:
        """Create or update a GitHub Release using `gh` CLI."""
        if not shutil.which("gh"):
            log_error("GitHub CLI (`gh`) is not installed. Cannot publish release.")
            return False

        existing_assets = [str(a) for a in assets if Path(a).exists()]
        if not existing_assets:
            log_warn("No assets to upload for GitHub release.")
            return False

        log_step(f"Publishing GitHub Release '{tag}': {release_title}...")
        
        # Check if release already exists
        check_res = run_cmd(["gh", "release", "view", tag, "-R", self.github_repo], check=False)
        if check_res.returncode == 0:
            # Edit existing release & upload assets
            cmd = ["gh", "release", "edit", tag, "-R", self.github_repo, "--title", release_title, "--notes", release_notes]
            run_cmd(cmd, check=True)
            upload_cmd = ["gh", "release", "upload", tag, "-R", self.github_repo, "--clobber"] + existing_assets
            run_cmd(upload_cmd, check=True)
        else:
            # Create new release
            cmd = ["gh", "release", "create", tag, "-R", self.github_repo, "--title", release_title, "--notes", release_notes] + existing_assets
            run_cmd(cmd, check=True)

        log_success(f"GitHub Release published: https://github.com/{self.github_repo}/releases/tag/{tag}")
        return True

    def prune_old_releases(self) -> None:
        """Prune older GitHub releases beyond keep_recent_count."""
        if not shutil.which("gh"):
            return

        log_info(f"Checking for old releases to prune (retention limit: {self.keep_recent_count})...")
        res = run_cmd(["gh", "release", "list", "-R", self.github_repo, "-L", "100"], check=False)
        if res.returncode != 0 or not res.stdout:
            return

        lines = res.stdout.strip().splitlines()
        if len(lines) > self.keep_recent_count:
            to_delete = lines[self.keep_recent_count:]
            for line in to_delete:
                tag = line.split("\t")[2] if len(line.split("\t")) >= 3 else line.split()[0]
                log_warn(f"Pruning older release: {tag}")
                run_cmd(["gh", "release", "delete", tag, "-R", self.github_repo, "--yes", "--cleanup-tag"], check=False)

    def send_telegram_notification(
        self,
        token: str,
        chat_id: str,
        message: str,
    ) -> bool:
        if not token or not chat_id:
            return False
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message[:4000],
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            log_warn(f"Telegram notification error: {e}")
            return False

    def send_discord_notification(self, webhook_url: str, message: str) -> bool:
        if not webhook_url:
            return False
        payload = {"content": message[:2000]}
        try:
            resp = requests.post(webhook_url, json=payload, timeout=10)
            return resp.status_code in (200, 204)
        except Exception as e:
            log_warn(f"Discord notification error: {e}")
            return False
