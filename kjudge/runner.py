"""
runner.py — Solution compilation, execution, and judging for kjudge.

Handles compiling solutions, running them against test inputs with
time limits, comparing outputs, and displaying verdict results.
"""

import os
import subprocess
import sys
import time

from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from kjudge.utils import (
    AC, WA, TLE, RTE,
    LAST_RUN_DIR,
    find_kjudge_dir, normalize_output,
    console, print_verdict, print_summary,
    print_error, print_success, print_info, print_warning,
)
from kjudge.config import load_config, apply_overrides
from kjudge.tests_store import (
    list_tests, load_test, resolve_test,
    get_tests_with_expected, get_tests_without_expected,
    get_next_index, save_test,
)


# ---------------------------------------------------------------------------
# Compilation
# ---------------------------------------------------------------------------
def compile_solution(build_cmd: str, cwd: str) -> tuple[bool, str]:
    """
    Run the build command. Returns (success, stderr_output).
    If build_cmd is empty, compilation is skipped (e.g. Python).
    """
    if not build_cmd or not build_cmd.strip():
        return True, ""

    try:
        result = subprocess.run(
            build_cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return False, result.stderr or result.stdout
        return True, result.stderr
    except subprocess.TimeoutExpired:
        return False, "Compilation timed out (30s limit)."
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------
class RunResult:
    """Result of running a solution on a single test."""
    __slots__ = ("stdout", "stderr", "time_ms", "exit_code", "verdict")

    def __init__(self, stdout="", stderr="", time_ms=0, exit_code=0, verdict=""):
        self.stdout = stdout
        self.stderr = stderr
        self.time_ms = time_ms
        self.exit_code = exit_code
        self.verdict = verdict


def run_solution(
    run_cmd: str,
    input_str: str,
    time_limit_ms: int,
    cwd: str,
) -> RunResult:
    """
    Run the solution with given input.
    Returns RunResult with stdout, stderr, time, exit code, and verdict hint.
    """
    timeout_sec = time_limit_ms / 1000.0

    try:
        start = time.perf_counter()
        result = subprocess.run(
            run_cmd,
            shell=True,
            cwd=cwd,
            input=input_str,
            capture_output=True,
            text=True,
            timeout=timeout_sec + 0.5,  # small grace period
        )
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        # Check TLE (even if process finished, check wall clock)
        if elapsed_ms > time_limit_ms:
            return RunResult(
                stdout=result.stdout,
                stderr=result.stderr,
                time_ms=elapsed_ms,
                exit_code=result.returncode,
                verdict=TLE,
            )

        # Check RTE
        if result.returncode != 0:
            return RunResult(
                stdout=result.stdout,
                stderr=result.stderr,
                time_ms=elapsed_ms,
                exit_code=result.returncode,
                verdict=RTE,
            )

        return RunResult(
            stdout=result.stdout,
            stderr=result.stderr,
            time_ms=elapsed_ms,
            exit_code=0,
            verdict="",  # caller decides AC/WA
        )

    except subprocess.TimeoutExpired:
        elapsed_ms = int(timeout_sec * 1000)
        return RunResult(
            stdout="", stderr="Time limit exceeded.",
            time_ms=elapsed_ms, exit_code=-1, verdict=TLE,
        )
    except Exception as e:
        return RunResult(
            stdout="", stderr=str(e),
            time_ms=0, exit_code=-1, verdict=RTE,
        )


# ---------------------------------------------------------------------------
# Judging
# ---------------------------------------------------------------------------
def judge_output(actual: str, expected: str, checker_cmd: str | None = None) -> str:
    """
    Compare actual vs expected output.
    Returns AC or WA. Delegates to checker if provided.
    """
    if checker_cmd:
        from kjudge.checker import run_checker
        return run_checker(checker_cmd, "", expected, actual)

    norm_actual = normalize_output(actual)
    norm_expected = normalize_output(expected)

    if norm_actual == norm_expected:
        return AC
    return WA


def save_last_run(base: str, test_name: str, actual_output: str):
    """Save last actual output for the diff command."""
    last_dir = os.path.join(base, LAST_RUN_DIR)
    os.makedirs(last_dir, exist_ok=True)
    path = os.path.join(last_dir, f"{test_name}.actual")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(actual_output)


# ---------------------------------------------------------------------------
# Running all tests
# ---------------------------------------------------------------------------
def run_all_tests(config: dict, base: str, args) -> tuple[int, int]:
    """
    Run all tests with expected output. Returns (passed, total).
    """
    test_names = get_tests_with_expected(base)
    if not test_names:
        print_warning("No tests with expected output found.")
        print_info("Use [bold]kjudge fetch[/], [bold]kjudge add[/], or [bold]kjudge answer[/] to create tests.")
        return 0, 0

    quiet = getattr(args, "quiet", False)
    show_input = getattr(args, "show_input", False)
    show_output = getattr(args, "show_output", False)
    checker = getattr(args, "checker", None)

    if not quiet:
        console.print(f"\n[bold]Running {len(test_names)} test(s)...[/]\n")

    passed = 0
    total = len(test_names)

    for name in test_names:
        input_str, expected = load_test(base, name)

        result = run_solution(
            config["run"],
            input_str,
            config.get("time_limit_ms", 2000),
            base,
        )

        # Determine verdict
        if result.verdict:
            verdict = result.verdict
        else:
            verdict = judge_output(result.stdout, expected, checker)

        if verdict == AC:
            passed += 1

        # Save for diff
        save_last_run(base, name, result.stdout)

        # Display
        print_verdict(name, verdict, result.time_ms, quiet)

        if show_input and not quiet:
            console.print(Panel(input_str.rstrip(), title="Input", border_style="dim"))

        if (show_output or verdict == WA) and not quiet:
            if verdict == WA:
                console.print(Panel(
                    f"[green]Expected:[/]\n{expected.rstrip()}\n\n"
                    f"[red]Actual:[/]\n{result.stdout.rstrip()}",
                    title=f"Output Mismatch — {name}",
                    border_style="red",
                ))

        if result.stderr and result.stderr.strip() and not quiet:
            console.print(f"    [dim]stderr: {result.stderr.strip()[:200]}[/]")

    print_summary(passed, total)
    return passed, total


def run_single_test(config: dict, base: str, test_name: str, args) -> str:
    """Run a single test, print result. Returns verdict."""
    input_str, expected = load_test(base, test_name)
    show_input = getattr(args, "show_input", False)
    show_output = getattr(args, "show_output", False)
    checker = getattr(args, "checker", None)

    console.print(f"\n[bold]Running test:[/] [cyan]{test_name}[/]\n")

    result = run_solution(
        config["run"],
        input_str,
        config.get("time_limit_ms", 2000),
        base,
    )

    if result.verdict:
        verdict = result.verdict
    elif expected is not None:
        verdict = judge_output(result.stdout, expected, checker)
    else:
        verdict = "?"
        print_info("No expected output — showing actual output only.")

    # Save for diff
    save_last_run(base, test_name, result.stdout)

    print_verdict(test_name, verdict, result.time_ms)

    if show_input:
        console.print(Panel(input_str.rstrip(), title="Input", border_style="dim"))

    if show_output or True:  # always show output for single test
        console.print(Panel(result.stdout.rstrip() or "(empty)", title="Output", border_style="blue"))

    if expected is not None and verdict == WA:
        console.print(Panel(expected.rstrip(), title="Expected", border_style="green"))

    if result.stderr and result.stderr.strip():
        console.print(Panel(result.stderr.strip(), title="Stderr", border_style="yellow"))

    return verdict


# ---------------------------------------------------------------------------
# CLI handlers
# ---------------------------------------------------------------------------
def handle_run(args):
    """Handle 'kjudge run' — run solution on all tests."""
    base = find_kjudge_dir()
    config = load_config(base)
    config = apply_overrides(config, args)

    # Check for interactive mode
    if getattr(args, "interactive", False):
        from kjudge.interactive import handle_interactive_run
        handle_interactive_run(config, base, args)
        return

    # Compile
    if config.get("build"):
        console.print(f"[dim]Compiling: {config['build']}[/]")
        ok, err = compile_solution(config["build"], base)
        if not ok:
            print_error("Compilation failed:")
            console.print(Panel(err.strip(), border_style="red"))
            sys.exit(1)
        print_success("Compiled successfully\n")

    run_all_tests(config, base, args)


def handle_case(args):
    """Handle 'kjudge case' — run a single test."""
    base = find_kjudge_dir()
    config = load_config(base)
    config = apply_overrides(config, args)

    test_name = resolve_test(base, args.test_id)

    # Compile
    if config.get("build"):
        console.print(f"[dim]Compiling: {config['build']}[/]")
        ok, err = compile_solution(config["build"], base)
        if not ok:
            print_error("Compilation failed:")
            console.print(Panel(err.strip(), border_style="red"))
            sys.exit(1)
        print_success("Compiled successfully")

    run_single_test(config, base, test_name, args)


def handle_gen(args):
    """Handle 'kjudge gen' — generate test inputs."""
    base = find_kjudge_dir()
    count = args.count
    gen_cmd = args.cmd

    console.print(f"\n[bold]Generating {count} test input(s)...[/]\n")

    generated = 0
    for i in range(count):
        idx = get_next_index(base, "gen")
        name = f"gen_{idx:03d}"

        try:
            result = subprocess.run(
                gen_cmd,
                shell=True,
                cwd=base,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                print_error(f"Generator failed on iteration {i+1}: {result.stderr.strip()}")
                continue

            save_test(base, name, result.stdout)
            generated += 1

        except subprocess.TimeoutExpired:
            print_error(f"Generator timed out on iteration {i+1}")
        except Exception as e:
            print_error(f"Generator error on iteration {i+1}: {e}")

    print_success(f"Generated {generated}/{count} test input(s)")
    print_info("Use [bold]kjudge answer[/] to fill expected outputs with a correct solution.")


def handle_answer(args):
    """Handle 'kjudge answer' — fill missing .out files."""
    base = find_kjudge_dir()
    config = load_config(base)
    config = apply_overrides(config, args)

    missing = get_tests_without_expected(base)
    if not missing:
        print_info("All tests already have expected output.")
        return

    # Compile
    if config.get("build"):
        console.print(f"[dim]Compiling: {config['build']}[/]")
        ok, err = compile_solution(config["build"], base)
        if not ok:
            print_error("Compilation failed:")
            console.print(Panel(err.strip(), border_style="red"))
            sys.exit(1)
        print_success("Compiled successfully\n")

    console.print(f"[bold]Filling expected output for {len(missing)} test(s)...[/]\n")

    filled = 0
    for name in missing:
        input_str, _ = load_test(base, name)

        result = run_solution(
            config["run"],
            input_str,
            config.get("time_limit_ms", 2000),
            base,
        )

        if result.verdict == TLE:
            print_warning(f"  {name}: TLE — skipped")
            continue
        if result.verdict == RTE:
            print_warning(f"  {name}: RTE — skipped")
            continue

        # Save the output
        from kjudge.tests_store import _tests_dir
        tdir = _tests_dir(base)
        out_path = os.path.join(tdir, f"{name}.out")
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(result.stdout)

        print_success(f"  {name}: output saved ({result.time_ms}ms)")
        filled += 1

    console.print(f"\n[bold green]Filled {filled}/{len(missing)} test(s)[/]")
