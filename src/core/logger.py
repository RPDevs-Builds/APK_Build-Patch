"""
Logging and GitHub Actions step annotation utility.
"""

import os
import sys
from rich.console import Console
from rich.theme import Theme

custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "step": "bold magenta",
})

console = Console(theme=custom_theme)

def is_github_actions() -> bool:
    return os.environ.get("GITHUB_ACTIONS") == "true"

def log_info(msg: str) -> None:
    console.print(f"[info][*][/info] {msg}")

def log_step(msg: str) -> None:
    console.print(f"\n[step]▶ {msg}[/step]")
    if is_github_actions():
        print(f"::group::{msg}", flush=True)

def log_end_step() -> None:
    if is_github_actions():
        print("::endgroup::", flush=True)

def log_warn(msg: str) -> None:
    console.print(f"[warning][!][/warning] {msg}", file=sys.stderr)
    if is_github_actions():
        print(f"::warning::{msg}", file=sys.stderr, flush=True)

def log_error(msg: str) -> None:
    console.print(f"[error][✗][/error] {msg}", file=sys.stderr)
    if is_github_actions():
        print(f"::error::{msg}", file=sys.stderr, flush=True)

def log_success(msg: str) -> None:
    console.print(f"[success][✓][/success] {msg}")
