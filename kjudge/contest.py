"""
contest.py — Contest scaffolding for kjudge.

Creates problem directories, initializes each with kjudge,
and fetches sample tests for an entire contest.
"""

import os
import sys
import argparse

from kjudge.utils import console, print_success, print_error, print_info
from kjudge.cf_fetcher import parse_cf_identifier, fetch_samples, fetch_contest_problems
from kjudge.config import get_defaults, save_config
from kjudge.tests_store import save_test
from kjudge.utils import ensure_kjudge_dir


def handle_contest(args):
    """Handle 'kjudge contest' — scaffold an entire contest."""
    identifier = args.identifier

    # Parse contest id
    if identifier.lower().startswith("cf:"):
        contest_id = identifier[3:].strip()
    else:
        contest_id = identifier.strip()

    # Remove any problem index from contest ID (e.g. "1234A" → "1234")
    import re
    match = re.match(r"^(\d+)", contest_id)
    if not match:
        print_error(f"Cannot parse contest ID: {contest_id}")
        sys.exit(1)
    contest_id = match.group(1)

    # Determine problems
    if args.problems:
        problems = [p.upper() for p in args.problems]
    else:
        console.print(f"[dim]Auto-detecting problems for contest {contest_id}...[/]")
        problems = fetch_contest_problems(contest_id)
        if not problems:
            print_error(
                "Could not auto-detect problems.\n"
                "  Use [bold]--problems A B C D[/] to specify manually."
            )
            sys.exit(1)

    # Determine language
    lang = args.lang or "cpp"
    defaults = get_defaults(lang)

    parent_dir = os.getcwd()

    console.print(
        f"\n[bold]Scaffolding contest[/] [cyan]{contest_id}[/] "
        f"with problems: [bold]{', '.join(problems)}[/]\n"
    )

    for problem in problems:
        problem_dir = os.path.join(parent_dir, problem)
        os.makedirs(problem_dir, exist_ok=True)

        # Init kjudge
        ensure_kjudge_dir(problem_dir)
        save_config(problem_dir, defaults)

        # Generate template if requested
        if args.template:
            from kjudge.templates import generate_template
            generate_template(lang, defaults["main_file"], problem_dir)

        # Fetch samples
        console.print(f"  [bold]{problem}[/]  ", end="")
        try:
            pairs = fetch_samples(contest_id, problem)
            for i, (inp, out) in enumerate(pairs, 1):
                name = f"sample_{i:03d}"
                save_test(problem_dir, name, inp, out)
            console.print(f"[green]✓[/] {len(pairs)} sample(s)")
        except SystemExit:
            console.print("[yellow]⚠ failed to fetch samples[/]")
        except Exception as e:
            console.print(f"[yellow]⚠ {e}[/]")

    console.print()
    print_success(
        f"Contest scaffolded! {len(problems)} problem directories created."
    )
    print_info(
        f"cd into any problem folder and run [bold]kjudge run {defaults['main_file']}[/]"
    )
