"""
Android Gradle Project Builder.
Clones open source Android repositories, runs Gradle builds, and extracts signed release APKs.
"""

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.logger import log_error, log_info, log_step, log_success, log_warn
from ..core.utils import find_java, run_cmd
from ..patchers.signer import APKSigner
from .base_builder import BaseBuilder

class GradleBuilder(BaseBuilder):
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

        # 1. Clone repository
        log_step(f"Cloning {repo_url} ({branch})...")
        if repo_dir.exists():
            shutil.rmtree(repo_dir, ignore_errors=True)
            
        clone_cmd = ["git", "clone", "--depth", "1", "--branch", branch, "--recurse-submodules", repo_url, str(repo_dir)]
        try:
            run_cmd(clone_cmd, check=True)
        except Exception:
            # Fallback if branch is a tag or commit
            clone_cmd = ["git", "clone", "--depth", "1", repo_url, str(repo_dir)]
            run_cmd(clone_cmd, check=True)
            run_cmd(["git", "checkout", branch], cwd=repo_dir, check=False)

        # 2. Check Gradle Wrapper
        gradlew = repo_dir / "gradlew"
        if not gradlew.exists():
            log_error(f"No gradlew script found in repository root: {repo_dir}")
            return []

        gradlew.chmod(0o755)

        # 3. Environment configuration (Java version, Android SDK)
        env = os.environ.copy()
        req_java = str(cfg.get("java_version", "21"))
        java_home_var = f"JAVA_HOME_{req_java}_X64"
        if java_home_var in env:
            env["JAVA_HOME"] = env[java_home_var]
            env["PATH"] = f"{env['JAVA_HOME']}/bin:{env['PATH']}"

        # 4. Run Gradle Build Task
        gradle_task = cfg.get("gradle_task", "assembleRelease")
        log_step(f"Executing Gradle build: ./gradlew {gradle_task} in {repo_name}...")
        
        build_cmd = ["./gradlew", gradle_task, "--no-daemon", "--stacktrace"]
        try:
            res = run_cmd(build_cmd, cwd=repo_dir, env=env, check=True)
            log_success(f"Gradle build completed successfully for {repo_name}")
        except Exception as e:
            log_error(f"Gradle build failed for {repo_name}: {e}")
            return []

        # 5. Locate and extract artifacts
        artifact_glob = cfg.get("artifact_glob", "**/build/outputs/apk/**/*.apk")
        found_apks = list(repo_dir.glob(artifact_glob))
        if not found_apks:
            # Fallback search for any built release APK
            found_apks = [p for p in repo_dir.glob("**/*.apk") if "release" in p.name.lower() or "unsigned" in p.name.lower()]

        if not found_apks:
            log_warn(f"No APK artifacts matching glob '{artifact_glob}' found in {repo_name}")
            return []

        built_apks = []
        for apk_path in found_apks:
            final_name = f"{repo_name}-{apk_path.name}"
            final_dest = out_d / final_name

            # If artifact is unsigned, sign it with our keystore
            if "unsigned" in apk_path.name.lower() or cfg.get("sign_artifacts", True):
                self.signer.sign_apk(apk_path, final_dest)
            else:
                shutil.copy2(apk_path, final_dest)

            built_apks.append(final_dest)
            log_success(f"Extracted artifact: {final_dest.name} ({final_dest.stat().st_size / (1024 * 1024):.2f} MB)")

        return built_apks
