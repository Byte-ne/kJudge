"""
watcher.py — File watch mode for kjudge.

Polls the solution file for modifications and auto-reruns
all tests on change. No external dependencies required.
"""

import os
import sys
import time
from datetime import datetime

from rich.panel import Panel

from kjudge.utils import find_kjudge_dir, console, print_info, print_error
from kjudge.config import load_config, apply_overrides
from kjudge.runner import compile_solution, run_all_tests


def handle_watch(args):
    """Handle 'kjudge watch' — auto-rerun tests on file changes."""
    base = find_kjudge_dir()
    config = load_config(base)
    config = apply_overrides(config, args)

    solution = args.solution_file or config.get("main_file")
    if not solution:
        print_error("No solution file specified. Pass it as argument or set in config.")
        sys.exit(1)

    filepath = os.path.join(base, solution)
    if not os.path.exists(filepath):
        print_error(f"File not found: {solution}")
        sys.exit(1)

    interval = getattr(args, "interval", 0.5)
    last_mtime = 0.0

    console.print(
        Panel(
            f"Watching [cyan]{solution}[/] for changes...\n"
            f"Press [bold]Ctrl+C[/] to stop.",
            title="👁 Watch Mode",
            border_style="blue",
        )
    )

    try:
        while True:
            try:
                current_mtime = os.path.getmtime(filepath)
            except OSError:
                time.sleep(interval)
                continue

            if current_mtime != last_mtime:
                last_mtime = current_mtime

                # Clear console
                os.system("cls" if os.name == "nt" else "clear")

                now = datetime.now().strftime("%H:%M:%S")
                console.print(
                    f"[dim]─── {now} ── File changed: {solution} ───[/]\n"
                )

                # Compile
                if config.get("build"):
                    console.print(f"[dim]Compiling: {config['build']}[/]")
                    ok, err = compile_solution(config["build"], base)
                    if not ok:
                        console.print(Panel(
                            err.strip(),
                            title="❌ Compilation Error",
                            border_style="red",
                        ))
                        console.print(f"\n[dim]Watching for changes...[/]")
                        time.sleep(interval)
                        continue
                    console.print("[green]✓[/] Compiled\n")

                # Run all tests
                run_all_tests(config, base, args)

                console.print(f"\n[dim]Watching for changes... (Ctrl+C to stop)[/]")

            time.sleep(interval)

    except KeyboardInterrupt:
        console.print("\n[bold]Watch mode stopped.[/]")
