"""
interactive.py — Interactive problem runner for kjudge.

Supports running interactive problems where the solution
communicates with a judge program via stdin/stdout pipes.
"""

import os
import subprocess
import sys
import threading
import time

from rich.panel import Panel

from kjudge.utils import (
    AC, WA, TLE, RTE,
    find_kjudge_dir, console, print_error, print_info, print_verdict,
)
from kjudge.tests_store import load_test, get_tests_with_expected


def handle_interactive_run(config: dict, base: str, args):
    """Run in interactive mode — solution talks to a judge program."""
    checker = getattr(args, "checker", None)

    if not checker:
        print_error(
            "Interactive mode requires a judge/interactor program.\n"
            "  Use: [bold]kjudge run --interactive --checker interactor.py[/]"
        )
        sys.exit(1)

    test_names = get_tests_with_expected(base)
    if not test_names:
        # For interactive, we can also use .in files without .out
        from kjudge.tests_store import list_tests
        all_tests = list_tests(base)
        test_names = [t["name"] for t in all_tests if t["has_in"]]

    if not test_names:
        print_info("No test inputs found.")
        return

    time_limit = config.get("time_limit_ms", 2000)
    run_cmd = config["run"]

    console.print(f"\n[bold]Interactive mode[/] — {len(test_names)} test(s)\n")
    console.print(f"  Solution:   [cyan]{run_cmd}[/]")
    console.print(f"  Interactor: [cyan]{checker}[/]\n")

    passed = 0
    total = len(test_names)

    for test_name in test_names:
        input_str, expected = load_test(base, test_name)

        verdict, time_ms, log = run_interactive_test(
            run_cmd, checker, input_str, time_limit, base,
        )

        if verdict == AC:
            passed += 1

        print_verdict(test_name, verdict, time_ms)

        if verdict != AC and log:
            console.print(Panel(
                log, title=f"Interaction Log — {test_name}",
                border_style="yellow",
            ))

    from kjudge.utils import print_summary
    print_summary(passed, total)


def run_interactive_test(
    solution_cmd: str,
    interactor_cmd: str,
    input_str: str,
    time_limit_ms: int,
    cwd: str,
) -> tuple[str, int, str]:
    """
    Run an interactive test.
    Returns (verdict, time_ms, interaction_log).

    The interactor receives the test input on stdin and
    communicates with the solution via pipes.
    """
    timeout_sec = time_limit_ms / 1000.0
    log_lines = []

    try:
        # Start solution process
        solution = subprocess.Popen(
            solution_cmd, shell=True, cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Start interactor with solution's stdin/stdout connected
        # Interactor gets test input on stdin
        interactor = subprocess.Popen(
            interactor_cmd, shell=True, cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Bridge: interactor stdout → solution stdin
        # Bridge: solution stdout → interactor stdin
        # This is done in threads

        solution_done = threading.Event()
        interactor_done = threading.Event()

        def pipe_interactor_to_solution():
            """Forward interactor output to solution input."""
            try:
                for line in interactor.stdout:
                    log_lines.append(f"J→S: {line.rstrip()}")
                    if solution.stdin and not solution.stdin.closed:
                        solution.stdin.write(line)
                        solution.stdin.flush()
            except (BrokenPipeError, OSError):
                pass
            finally:
                try:
                    if solution.stdin and not solution.stdin.closed:
                        solution.stdin.close()
                except OSError:
                    pass

        def pipe_solution_to_interactor():
            """Forward solution output to interactor input."""
            try:
                for line in solution.stdout:
                    log_lines.append(f"S→J: {line.rstrip()}")
                    if interactor.stdin and not interactor.stdin.closed:
                        interactor.stdin.write(line)
                        interactor.stdin.flush()
            except (BrokenPipeError, OSError):
                pass
            finally:
                try:
                    if interactor.stdin and not interactor.stdin.closed:
                        interactor.stdin.close()
                except OSError:
                    pass

        # Send test input to interactor
        if input_str:
            try:
                interactor.stdin.write(input_str)
                interactor.stdin.flush()
            except (BrokenPipeError, OSError):
                pass

        t1 = threading.Thread(target=pipe_interactor_to_solution, daemon=True)
        t2 = threading.Thread(target=pipe_solution_to_interactor, daemon=True)

        start = time.perf_counter()
        t1.start()
        t2.start()

        # Wait for both to finish
        solution.wait(timeout=timeout_sec)
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        # Give interactor a moment to finish
        try:
            interactor.wait(timeout=2)
        except subprocess.TimeoutExpired:
            interactor.kill()

        t1.join(timeout=1)
        t2.join(timeout=1)

        # Determine verdict
        if elapsed_ms > time_limit_ms:
            return TLE, elapsed_ms, "\n".join(log_lines)

        if solution.returncode != 0:
            return RTE, elapsed_ms, "\n".join(log_lines)

        # Interactor exit 0 = AC
        if interactor.returncode == 0:
            return AC, elapsed_ms, "\n".join(log_lines)
        else:
            return WA, elapsed_ms, "\n".join(log_lines)

    except subprocess.TimeoutExpired:
        try:
            solution.kill()
        except Exception:
            pass
        try:
            interactor.kill()
        except Exception:
            pass
        return TLE, time_limit_ms, "\n".join(log_lines)

    except Exception as e:
        return RTE, 0, f"Error: {e}"
