"""
Unified Command Line Interface for RPDevs APK Engine & Vault.
"""

import argparse
import sys
from pathlib import Path

from .core.config_loader import load_config
from .core.logger import log_error, log_info, log_step, log_success
from .core.runner import PipelineRunner

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="apk-engine",
        description="RPDevs APK Engine - Universal ReVanced/Morphe Patcher, Repo Builder & Storage Hub",
    )
    parser.add_argument(
        "--config-dir",
        "-c",
        type=str,
        default=None,
        help="Path to configuration directory (defaults to ./config)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. Patch Command
    patch_parser = subparsers.add_parser("patch", help="Run ReVanced/Morphe APK patching pipeline")
    patch_parser.add_argument("--app", "-a", type=str, default=None, help="Target app name to patch (e.g. YouTube)")

    # 2. Build Command
    build_parser = subparsers.add_parser("build", help="Build open-source repositories from source")
    build_parser.add_argument("--repo", "-r", type=str, default=None, help="Specific repo name or URL to build")

    # 3. Storage Hub Command
    storage_parser = subparsers.add_parser("storage", help="Generate F-Droid repo, Web Portal, Obtainium feed, and Magisk OTA")
    storage_parser.add_argument("--tag", "-t", type=str, default="latest", help="Release tag for asset links")

    # 4. Run-All Pipeline
    all_parser = subparsers.add_parser("run-all", help="Execute complete CI/CD pipeline (patch, build, index, portal)")
    all_parser.add_argument("--tag", "-t", type=str, default="latest", help="Release tag")

    args = parser.parse_args()
    runner = PipelineRunner(config_dir=args.config_dir)

    try:
        if args.command == "patch":
            runner.run_patching_pipeline(target_app=args.app)
        elif args.command == "build":
            runner.run_repo_builds(target_repo=args.repo)
        elif args.command == "storage":
            runner.generate_storage_hub(release_tag=args.tag)
        elif args.command == "run-all":
            log_step("Executing Full CI/CD Pipeline...")
            runner.run_patching_pipeline()
            runner.run_repo_builds()
            runner.generate_storage_hub(release_tag=args.tag)
            log_success("Full CI/CD Pipeline execution completed.")
    except Exception as e:
        log_error(f"Execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
