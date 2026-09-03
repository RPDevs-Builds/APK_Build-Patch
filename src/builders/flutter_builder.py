"""
Flutter & React Native Open-Source Android App Builders.
"""

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.logger import log_error, log_info, log_step, log_success
from ..core.utils import run_cmd
from ..patchers.signer import APKSigner
from .base_builder import BaseBuilder

class FlutterBuilder(BaseBuilder):
    def __init__(self, workspace_dir: Path | str = "temp/build_workspace"):
        super().__init__(workspace_dir)
        self.signer = APKSigner()

    def build_from_source(
        self,
        repo_url: str,
        branch: str = "main",
        output_dir: Path | str = "dist/apks",
        config: Optional[Dict[str, Any]] = None,
    ) -> List[Path]:
        cfg = config or {}
        repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        repo_dir = self.workspace_dir / repo_name
        out_d = Path(output_dir)
        out_d.mkdir(parents=True, exist_ok=True)

        if repo_dir.exists():
            shutil.rmtree(repo_dir, ignore_errors=True)

        log_step(f"Cloning Flutter project: {repo_url}...")
        run_cmd(["git", "clone", "--depth", "1", "--branch", branch, repo_url, str(repo_dir)], check=True)

        log_step(f"Building Flutter APK in {repo_name}...")
        run_cmd(["flutter", "pub", "get"], cwd=repo_dir, check=True)
        run_cmd(["flutter", "build", "apk", "--release"], cwd=repo_dir, check=True)

        found_apks = list(repo_dir.glob("build/app/outputs/flutter-apk/*.apk"))
        built_apks = []
        for apk in found_apks:
            dest = out_d / f"{repo_name}-{apk.name}"
            self.signer.sign_apk(apk, dest)
            built_apks.append(dest)
        return built_apks


class ReactNativeBuilder(BaseBuilder):
    def __init__(self, workspace_dir: Path | str = "temp/build_workspace"):
        super().__init__(workspace_dir)
        self.signer = APKSigner()

    def build_from_source(
        self,
        repo_url: str,
        branch: str = "main",
        output_dir: Path | str = "dist/apks",
        config: Optional[Dict[str, Any]] = None,
    ) -> List[Path]:
        cfg = config or {}
        repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        repo_dir = self.workspace_dir / repo_name
        out_d = Path(output_dir)
        out_d.mkdir(parents=True, exist_ok=True)

        if repo_dir.exists():
            shutil.rmtree(repo_dir, ignore_errors=True)

        log_step(f"Cloning React Native project: {repo_url}...")
        run_cmd(["git", "clone", "--depth", "1", "--branch", branch, repo_url, str(repo_dir)], check=True)

        log_step(f"Installing dependencies and building RN Android APK...")
        if (repo_dir / "yarn.lock").exists():
            run_cmd(["yarn", "install", "--frozen-lockfile"], cwd=repo_dir, check=True)
        else:
            run_cmd(["npm", "ci"], cwd=repo_dir, check=True)

        android_dir = repo_dir / "android"
        if not android_dir.exists():
            log_error(f"No android directory found in React Native repo: {repo_dir}")
            return []

        gradlew = android_dir / "gradlew"
        if gradlew.exists():
            gradlew.chmod(0o755)
            run_cmd(["./gradlew", "assembleRelease", "--no-daemon"], cwd=android_dir, check=True)

        found_apks = list(android_dir.glob("app/build/outputs/apk/release/*.apk"))
        built_apks = []
        for apk in found_apks:
            dest = out_d / f"{repo_name}-{apk.name}"
            self.signer.sign_apk(apk, dest)
            built_apks.append(dest)
        return built_apks
