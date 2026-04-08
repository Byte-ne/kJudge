"""
stress.py — Stress testing engine for kjudge.

Runs a generator, feeds output to both a brute-force and an optimized
solution, and finds the first input where they disagree.
"""

import subprocess
import sys
import os

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel

from kjudge.utils import (
    find_kjudge_dir, normalize_output,
    console, print_error, print_success, print_info, print_warning,
)
from kjudge.config import load_config, apply_overrides, get_defaults
from kjudge.runner import compile_solution, run_solution
from kjudge.tests_store import save_test, get_next_index


def _get_run_cmd(filepath: str, config: dict) -> tuple[str, str]:
    """
    Determine build and run commands for a given file.
    Returns (build_cmd, run_cmd).
    """
    ext = os.path.splitext(filepath)[1].lower()
    lang_map = {".cpp": "cpp", ".cc": "cpp", ".java": "java", ".py": "python"}
    lang = lang_map.get(ext, config.get("language", "cpp"))
    defaults = get_defaults(lang, filepath)
    return defaults["build"], defaults["run"]


def handle_stress(args):
    """Handle 'kjudge stress' — find counterexample between two solutions."""
    base = find_kjudge_dir()
    config = load_config(base)
    config = apply_overrides(config, args)

    brute_file = args.brute
    smart_file = args.smart
    gen_cmd = args.gen
    max_iter = args.max
    time_limit = config.get("time_limit_ms", 2000)

    # Check files exist
    for f in [brute_file, smart_file]:
        if not os.path.exists(os.path.join(base, f)):
            print_error(f"File not found: {f}")
            sys.exit(1)

    console.print(f"\n[bold]Stress Testing[/]")
    console.print(f"  Brute:     [cyan]{brute_file}[/]")
    console.print(f"  Smart:     [cyan]{smart_file}[/]")
    console.print(f"  Generator: [cyan]{gen_cmd}[/]")
    console.print(f"  Max iters: [cyan]{max_iter}[/]")
    console.print()

    # Compile both solutions
    brute_build, brute_run = _get_run_cmd(brute_file, config)
    smart_build, smart_run = _get_run_cmd(smart_file, config)

    if brute_build:
        console.print(f"[dim]Compiling brute: {brute_build}[/]")
        ok, err = compile_solution(brute_build, base)
        if not ok:
            print_error(f"Brute compilation failed:\n{err}")
            sys.exit(1)

    if smart_build:
        # Need different executable names to avoid collision
        # Adjust build command for smart solution
        smart_build_adj = smart_build
        is_win = os.name == "nt"
        if "cpp" in smart_file or "cc" in smart_file:
            smart_exe = "smart.exe" if is_win else "./smart"
            smart_build_adj = f"g++ -std=c++17 -O2 -o {'smart'} {smart_file}"
            smart_run = smart_exe
        console.print(f"[dim]Compiling smart: {smart_build_adj}[/]")
        ok, err = compile_solution(smart_build_adj, base)
        if not ok:
            print_error(f"Smart compilation failed:\n{err}")
            sys.exit(1)

    # Also need brute with different name
    if brute_build and ("cpp" in brute_file or "cc" in brute_file):
        is_win = os.name == "nt"
        brute_exe = "brute.exe" if is_win else "./brute"
        brute_build_adj = f"g++ -std=c++17 -O2 -o {'brute'} {brute_file}"
        console.print(f"[dim]Compiling brute: {brute_build_adj}[/]")
        ok, err = compile_solution(brute_build_adj, base)
        if not ok:
            print_error(f"Brute compilation failed:\n{err}")
            sys.exit(1)
        brute_run = brute_exe

    print_success("Both solutions compiled\n")

    # Stress test loop
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        console=console,
    ) as progress:
        task = progress.add_task("Testing...", total=max_iter)

        for i in range(1, max_iter + 1):
            progress.update(task, description=f"Iteration {i}")

            # Generate input
            try:
                gen_result = subprocess.run(
                    gen_cmd, shell=True, cwd=base,
                    capture_output=True, text=True, timeout=10,
                )
                if gen_result.returncode != 0:
                    print_error(f"Generator failed at iteration {i}")
                    return
                test_input = gen_result.stdout
            except subprocess.TimeoutExpired:
                print_error(f"Generator timed out at iteration {i}")
                return

            # Run brute
            brute_result = run_solution(brute_run, test_input, time_limit * 2, base)
            if brute_result.verdict:
                print_warning(f"Brute got {brute_result.verdict} at iteration {i}, skipping")
                progress.advance(task)
                continue

            # Run smart
            smart_result = run_solution(smart_run, test_input, time_limit, base)

            # Compare
            brute_out = normalize_output(brute_result.stdout)
            smart_out = normalize_output(smart_result.stdout)

            if smart_result.verdict or brute_out != smart_out:
                progress.stop()

                verdict = smart_result.verdict or "WA"
                console.print(
                    f"\n[bold red]🔥 COUNTEREXAMPLE FOUND![/] "
                    f"(iteration {i}, verdict: {verdict})\n"
                )

                # Save the counterexample
                idx = get_next_index(base, "stress")
                name = f"stress_{idx:03d}"
                save_test(base, name, test_input, brute_result.stdout)

                # Display
                console.print(Panel(
                    test_input.rstrip(),
                    title="📥 Input",
                    border_style="blue",
                ))
                console.print(Panel(
                    brute_result.stdout.rstrip(),
                    title="✓ Brute Output (expected)",
                    border_style="green",
                ))
                console.print(Panel(
                    smart_result.stdout.rstrip() or f"({verdict})",
                    title="✗ Smart Output (actual)",
                    border_style="red",
                ))

                print_success(
                    f"Saved as [cyan]{name}[/] — "
                    f"use [bold]kjudge diff {name}[/] for details"
                )
                return

            progress.advance(task)

    console.print(
        f"\n[bold green]✓ All {max_iter} iterations passed![/] "
        "No counterexample found."
    )
