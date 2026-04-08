"""
tests_store.py — Test case file management for kjudge.

Handles reading, writing, listing, and organizing .in/.out test files
under .kjudge/tests/. Supports sample_, custom_, gen_, and stress_ prefixes.
"""

import os
import glob
import sys

from rich.table import Table

from kjudge.utils import (
    TESTS_DIR, find_kjudge_dir, console, print_success, print_info,
    print_error, print_warning,
)


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------
def _tests_dir(base: str | None = None) -> str:
    """Return the absolute path to .kjudge/tests/."""
    base = base or find_kjudge_dir()
    return os.path.join(base, TESTS_DIR)


def list_tests(base: str | None = None) -> list[dict]:
    """
    List all test cases with metadata.
    Returns sorted list of dicts: {name, has_in, has_out, in_size, out_size}.
    """
    tdir = _tests_dir(base)
    if not os.path.isdir(tdir):
        return []

    # Collect unique test names
    names = set()
    for f in os.listdir(tdir):
        if f.endswith(".in") or f.endswith(".out"):
            name = f.rsplit(".", 1)[0]
            names.add(name)

    results = []
    for name in sorted(names):
        in_path = os.path.join(tdir, f"{name}.in")
        out_path = os.path.join(tdir, f"{name}.out")
        results.append({
            "name": name,
            "has_in": os.path.exists(in_path),
            "has_out": os.path.exists(out_path),
            "in_size": os.path.getsize(in_path) if os.path.exists(in_path) else 0,
            "out_size": os.path.getsize(out_path) if os.path.exists(out_path) else 0,
        })

    return results


def get_next_index(base: str, prefix: str) -> int:
    """Get the next available index for a given prefix (e.g. 'custom' → 3)."""
    tdir = _tests_dir(base)
    existing = []
    if os.path.isdir(tdir):
        for f in os.listdir(tdir):
            if f.startswith(prefix + "_") and f.endswith(".in"):
                # e.g. custom_003.in → 3
                try:
                    idx = int(f[len(prefix)+1:].split(".")[0])
                    existing.append(idx)
                except ValueError:
                    pass
    return max(existing, default=0) + 1


def save_test(base: str, name: str, input_str: str, output_str: str | None = None):
    """Save a test case (.in and optionally .out)."""
    tdir = _tests_dir(base)
    os.makedirs(tdir, exist_ok=True)

    in_path = os.path.join(tdir, f"{name}.in")
    with open(in_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(input_str)

    if output_str is not None:
        out_path = os.path.join(tdir, f"{name}.out")
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(output_str)


def load_test(base: str, name: str) -> tuple[str, str | None]:
    """Load a test case. Returns (input_str, expected_output_or_None)."""
    tdir = _tests_dir(base)
    in_path = os.path.join(tdir, f"{name}.in")
    out_path = os.path.join(tdir, f"{name}.out")

    if not os.path.exists(in_path):
        print_error(f"Test input not found: {in_path}")
        sys.exit(1)

    with open(in_path, "r", encoding="utf-8") as f:
        input_str = f.read()

    output_str = None
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            output_str = f.read()

    return input_str, output_str


def resolve_test(base: str, identifier: str) -> str:
    """
    Resolve a test identifier (index or name) to a test name.
    - If identifier is a number, return the Nth test in sorted order.
    - Otherwise, return the identifier as-is if it exists.
    """
    tests = list_tests(base)
    if not tests:
        print_error("No test cases found.")
        sys.exit(1)

    # Try as numeric index
    try:
        idx = int(identifier)
        if 1 <= idx <= len(tests):
            return tests[idx - 1]["name"]
        else:
            print_error(f"Test index {idx} out of range (1-{len(tests)}).")
            sys.exit(1)
    except ValueError:
        pass

    # Try as exact name
    names = [t["name"] for t in tests]
    if identifier in names:
        return identifier

    # Try partial match
    matches = [n for n in names if identifier in n]
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        print_error(
            f"Ambiguous test name '{identifier}'. Matches: {', '.join(matches)}"
        )
        sys.exit(1)

    print_error(f"Test '{identifier}' not found.")
    sys.exit(1)


def get_tests_with_expected(base: str) -> list[str]:
    """Return names of tests that have both .in and .out."""
    return [t["name"] for t in list_tests(base) if t["has_in"] and t["has_out"]]


def get_tests_without_expected(base: str) -> list[str]:
    """Return names of tests that have .in but no .out."""
    return [t["name"] for t in list_tests(base) if t["has_in"] and not t["has_out"]]


def remove_test(base: str, name: str):
    """Delete both .in and .out for a test case."""
    tdir = _tests_dir(base)
    removed = False
    for ext in (".in", ".out"):
        path = os.path.join(tdir, f"{name}{ext}")
        if os.path.exists(path):
            os.remove(path)
            removed = True
    return removed


def clean_tests(base: str, category: str) -> int:
    """
    Remove tests by category. Returns count of tests removed.
    category: 'all', 'gen', 'custom', 'samples', 'stress'
    """
    tdir = _tests_dir(base)
    if not os.path.isdir(tdir):
        return 0

    count = 0
    prefix_map = {
        "gen": "gen_",
        "custom": "custom_",
        "samples": "sample_",
        "stress": "stress_",
    }

    for f in os.listdir(tdir):
        should_remove = False
        if category == "all":
            should_remove = True
        elif category in prefix_map:
            should_remove = f.startswith(prefix_map[category])

        if should_remove and (f.endswith(".in") or f.endswith(".out")):
            os.remove(os.path.join(tdir, f))
            if f.endswith(".in"):
                count += 1

    return count


# ---------------------------------------------------------------------------
# CLI handlers
# ---------------------------------------------------------------------------
def handle_add(args):
    """Handle 'kjudge add' — interactively add a custom test case."""
    base = find_kjudge_dir()
    idx = get_next_index(base, "custom")
    name = f"custom_{idx:03d}"

    console.print(f"\n[bold]Adding test case:[/] [cyan]{name}[/]\n")

    # Read input
    console.print("[bold]Enter input[/] (end with an empty line):")
    lines = []
    while True:
        try:
            line = input()
            if line == "":
                break
            lines.append(line)
        except EOFError:
            break
    input_str = "\n".join(lines) + "\n" if lines else ""

    # Read expected output
    console.print("\n[bold]Enter expected output[/] (end with an empty line):")
    lines = []
    while True:
        try:
            line = input()
            if line == "":
                break
            lines.append(line)
        except EOFError:
            break
    output_str = "\n".join(lines) + "\n" if lines else ""

    save_test(base, name, input_str, output_str if output_str.strip() else None)

    has_out = bool(output_str.strip())
    print_success(
        f"Saved [cyan]{name}[/] "
        f"({'with' if has_out else 'without'} expected output)"
    )


def handle_list(args):
    """Handle 'kjudge list' — show all test cases in a table."""
    base = find_kjudge_dir()
    tests = list_tests(base)

    if not tests:
        print_info("No test cases found. Use [bold]kjudge add[/] or [bold]kjudge fetch[/].")
        return

    table = Table(title="Test Cases", show_lines=False)
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Name", style="bold cyan")
    table.add_column("Input", justify="center")
    table.add_column("Output", justify="center")
    table.add_column("In Size", justify="right", style="dim")
    table.add_column("Out Size", justify="right", style="dim")

    for i, t in enumerate(tests, 1):
        in_mark = "[green]✓[/]" if t["has_in"] else "[red]✗[/]"
        out_mark = "[green]✓[/]" if t["has_out"] else "[yellow]—[/]"
        in_size = _format_size(t["in_size"]) if t["has_in"] else "—"
        out_size = _format_size(t["out_size"]) if t["has_out"] else "—"
        table.add_row(str(i), t["name"], in_mark, out_mark, in_size, out_size)

    console.print()
    console.print(table)
    console.print(f"\n  [dim]{len(tests)} test(s) total[/]")


def handle_remove(args):
    """Handle 'kjudge remove' — delete a specific test case."""
    base = find_kjudge_dir()
    name = resolve_test(base, args.test_id)

    if remove_test(base, name):
        print_success(f"Removed test [cyan]{name}[/]")
    else:
        print_error(f"Test '{name}' not found.")


def handle_clean(args):
    """Handle 'kjudge clean' — remove test cases by category."""
    base = find_kjudge_dir()

    if args.gen:
        category = "gen"
    elif args.custom:
        category = "custom"
    elif args.samples:
        category = "samples"
    elif args.build:
        # Clean build artifacts
        _clean_build(base)
        return
    elif args.all:
        category = "all"
    else:
        # Default: ask
        from rich.prompt import Confirm
        if Confirm.ask("[bold yellow]Remove ALL tests and build artifacts?[/]"):
            category = "all"
            _clean_build(base)
        else:
            return

    count = clean_tests(base, category)
    if count > 0:
        print_success(f"Removed {count} {category} test(s)")
    else:
        print_info(f"No {category} tests to remove.")


def _clean_build(base: str):
    """Remove build artifacts (compiled files)."""
    removed = 0
    for pattern in ["main", "main.exe", "*.class", "__pycache__"]:
        for f in glob.glob(os.path.join(base, pattern)):
            if os.path.isfile(f):
                os.remove(f)
                removed += 1
            elif os.path.isdir(f):
                import shutil
                shutil.rmtree(f)
                removed += 1
    if removed:
        print_success(f"Removed {removed} build artifact(s)")
    else:
        print_info("No build artifacts to remove.")


def _format_size(size_bytes: int) -> str:
    """Format file size nicely."""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f}MB"
