"""
utils.py — Shared helpers for kjudge.

Provides output normalization, .kjudge directory discovery,
and Rich-based printing utilities for verdicts and summaries.
"""

import os
import sys
from pathlib import Path

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.table import Table

console = Console()
error_console = Console(stderr=True)

# ---------------------------------------------------------------------------
# Verdict constants
# ---------------------------------------------------------------------------
AC = "AC"
WA = "WA"
TLE = "TLE"
RTE = "RTE"

VERDICT_STYLES = {
    AC: "bold green",
    WA: "bold red",
    TLE: "bold yellow",
    RTE: "bold magenta",
}

# ---------------------------------------------------------------------------
# Directory helpers
# ---------------------------------------------------------------------------
KJUDGE_DIR = ".kjudge"
TESTS_DIR = os.path.join(KJUDGE_DIR, "tests")
LAST_RUN_DIR = os.path.join(KJUDGE_DIR, "last_run")
CONFIG_FILE = os.path.join(KJUDGE_DIR, "config.json")
GLOBAL_DIR = os.path.join(Path.home(), ".kjudge")
GLOBAL_CONFIG = os.path.join(GLOBAL_DIR, "config.json")
TEMPLATES_DIR = os.path.join(GLOBAL_DIR, "templates")


def find_kjudge_dir(cwd: str | None = None) -> str:
    """
    Locate the .kjudge directory starting from *cwd* (default: os.getcwd()).
    Raises SystemExit with a helpful message if not found.
    """
    start = cwd or os.getcwd()
    path = os.path.abspath(start)
    kjudge_path = os.path.join(path, KJUDGE_DIR)
    if os.path.isdir(kjudge_path):
        return path
    # Don't walk up — kjudge expects to be run inside the problem dir
    error_console.print(
        f"[bold red]Error:[/] No .kjudge directory found in [cyan]{path}[/].\n"
        "Run [bold]kjudge init[/] first to set up this problem directory."
    )
    sys.exit(1)


def ensure_kjudge_dir(cwd: str | None = None) -> str:
    """Return the .kjudge path, creating tests dir if needed."""
    base = cwd or os.getcwd()
    kjudge = os.path.join(base, KJUDGE_DIR)
    tests = os.path.join(base, TESTS_DIR)
    last_run = os.path.join(base, LAST_RUN_DIR)
    os.makedirs(tests, exist_ok=True)
    os.makedirs(last_run, exist_ok=True)
    return base


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------
def normalize_output(text: str) -> str:
    """
    Normalize solution output for comparison:
    - Convert \\r\\n to \\n
    - Strip trailing spaces on each line
    - Strip trailing newline
    """
    text = text.replace("\r\n", "\n")
    lines = text.split("\n")
    lines = [line.rstrip() for line in lines]
    # Remove trailing empty lines
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Pretty printing
# ---------------------------------------------------------------------------
def print_verdict(test_name: str, verdict: str, time_ms: int, quiet: bool = False):
    """Print a single test verdict line with color."""
    style = VERDICT_STYLES.get(verdict, "")
    v = Text(f" {verdict} ", style=f"{style} reverse")
    time_str = f"{time_ms}ms"
    if quiet:
        return
    console.print(
        Text(f"  {test_name:<25}", style="bold"),
        v,
        Text(f"  {time_str}", style="dim"),
    )


def print_summary(passed: int, total: int):
    """Print the final summary line."""
    if total == 0:
        console.print("\n[dim]No tests found.[/]")
        return
    color = "green" if passed == total else "red"
    console.print(
        f"\n[bold {color}]  {passed}/{total} tests passed[/]"
    )


def print_error(msg: str):
    """Print an error message to stderr."""
    error_console.print(f"[bold red]Error:[/] {msg}")


def print_success(msg: str):
    """Print a success message."""
    console.print(f"[bold green]✓[/] {msg}")


def print_info(msg: str):
    """Print an info message."""
    console.print(f"[bold blue]ℹ[/] {msg}")


def print_warning(msg: str):
    """Print a warning message."""
    console.print(f"[bold yellow]⚠[/] {msg}")
