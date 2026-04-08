"""
diff_view.py — Colored diff display for kjudge.

Shows side-by-side comparison of expected vs actual output
with unified diff highlighting using Rich panels.
"""

import difflib
import os

from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich.syntax import Syntax

from kjudge.utils import (
    LAST_RUN_DIR,
    find_kjudge_dir, normalize_output,
    console, print_error, print_info,
)
from kjudge.tests_store import load_test, resolve_test


def _build_diff_text(expected: str, actual: str) -> Text:
    """Build a Rich Text object from unified diff output."""
    exp_lines = normalize_output(expected).splitlines(keepends=True)
    act_lines = normalize_output(actual).splitlines(keepends=True)

    diff = difflib.unified_diff(
        exp_lines, act_lines,
        fromfile="expected", tofile="actual",
        lineterm="",
    )

    result = Text()
    for line in diff:
        line = line.rstrip("\n")
        if line.startswith("+++") or line.startswith("---"):
            result.append(line + "\n", style="bold")
        elif line.startswith("@@"):
            result.append(line + "\n", style="cyan")
        elif line.startswith("+"):
            result.append(line + "\n", style="green")
        elif line.startswith("-"):
            result.append(line + "\n", style="red")
        else:
            result.append(line + "\n", style="dim")

    return result


def show_diff(
    test_name: str,
    input_str: str | None,
    expected: str,
    actual: str,
    show_input: bool = False,
):
    """Display a colored diff for a test case."""
    console.print(f"\n[bold]Diff for test:[/] [cyan]{test_name}[/]\n")

    if show_input and input_str:
        console.print(Panel(
            input_str.rstrip(),
            title="📥 Input",
            border_style="blue",
        ))

    # Side by side: expected vs actual
    exp_panel = Panel(
        expected.rstrip() or "(empty)",
        title="✓ Expected Output",
        border_style="green",
        width=50,
    )
    act_panel = Panel(
        actual.rstrip() or "(empty)",
        title="✗ Actual Output",
        border_style="red",
        width=50,
    )
    console.print(Columns([exp_panel, act_panel], padding=2))

    # Unified diff
    norm_exp = normalize_output(expected)
    norm_act = normalize_output(actual)

    if norm_exp == norm_act:
        console.print("[bold green]  ✓ Outputs match (AC)[/]")
        return

    diff_text = _build_diff_text(expected, actual)
    if diff_text.plain.strip():
        console.print(Panel(
            diff_text,
            title="📊 Unified Diff",
            border_style="yellow",
        ))

    # Line-by-line comparison summary
    exp_lines = norm_exp.splitlines()
    act_lines = norm_act.splitlines()
    max_lines = max(len(exp_lines), len(act_lines))

    mismatch_count = 0
    for i in range(max_lines):
        e = exp_lines[i] if i < len(exp_lines) else "(missing)"
        a = act_lines[i] if i < len(act_lines) else "(missing)"
        if e != a:
            mismatch_count += 1

    console.print(
        f"\n  [bold red]{mismatch_count}[/] line(s) differ "
        f"out of [bold]{max_lines}[/] total"
    )


# ---------------------------------------------------------------------------
# CLI handler
# ---------------------------------------------------------------------------
def handle_diff(args):
    """Handle 'kjudge diff' — show diff for a test case."""
    base = find_kjudge_dir()
    test_name = resolve_test(base, args.test_id)

    input_str, expected = load_test(base, test_name)

    if expected is None:
        print_error(
            f"Test [cyan]{test_name}[/] has no expected output (.out file).\n"
            "  Cannot show diff without expected output."
        )
        return

    # Load last actual output
    actual_path = os.path.join(base, LAST_RUN_DIR, f"{test_name}.actual")
    if not os.path.exists(actual_path):
        print_error(
            f"No last-run output found for [cyan]{test_name}[/].\n"
            "  Run [bold]kjudge run[/] or [bold]kjudge case {test_name}[/] first."
        )
        return

    with open(actual_path, "r", encoding="utf-8") as f:
        actual = f.read()

    show_input = getattr(args, "show_input", False)
    show_diff(test_name, input_str, expected, actual, show_input)
