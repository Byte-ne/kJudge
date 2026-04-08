"""
cli.py — Entrypoint and command dispatch for kjudge.

Defines a git-style CLI with argparse subcommands.
Each subcommand delegates to its handler function.
"""

import argparse
import sys

from kjudge import __version__


def _add_solution_arg(parser: argparse.ArgumentParser):
    """Add optional solution_file positional arg used by run/case/answer."""
    parser.add_argument(
        "solution_file", nargs="?", default=None,
        help="Solution file to compile & run (e.g. main.cpp). "
             "If omitted, uses the file from config.",
    )


def _add_run_options(parser: argparse.ArgumentParser):
    """Add shared options for run/case commands."""
    parser.add_argument("--lang", choices=["cpp", "java", "python"],
                        help="Override language from config.")
    parser.add_argument("--time", type=int, metavar="MS",
                        help="Time limit in milliseconds (default: from config).")
    parser.add_argument("--mem", type=int, metavar="MB",
                        help="Memory limit in MB (default: from config).")
    parser.add_argument("--quiet", action="store_true",
                        help="Only print summary, not individual test results.")
    parser.add_argument("--show-input", action="store_true",
                        help="Show test input for each run.")
    parser.add_argument("--hide-input", action="store_true",
                        help="Hide test input (default).")
    parser.add_argument("--show-output", action="store_true",
                        help="Show actual output for each run.")
    parser.add_argument("--hide-output", action="store_true",
                        help="Hide actual output (default).")
    parser.add_argument("--checker", metavar="CMD",
                        help="Custom checker command or built-in name "
                             "(e.g. 'python checker.py', 'token', 'float:1e-6').")
    parser.add_argument("--interactive", action="store_true",
                        help="Run in interactive mode (solution talks to judge via pipes).")


def build_parser() -> argparse.ArgumentParser:
    """Build and return the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="kjudge",
        description="kjudge — Competitive programming local judge.",
        epilog="Run 'kjudge <command> --help' for details on each command.",
    )
    parser.add_argument(
        "--version", action="version", version=f"kjudge {__version__}"
    )

    sub = parser.add_subparsers(dest="command", title="commands")

    # ── 1. init ──────────────────────────────────────────────────────────
    p_init = sub.add_parser(
        "init",
        help="Initialize a problem directory with .kjudge config.",
        description="Create .kjudge/ directory and config.json interactively.",
    )
    p_init.add_argument(
        "--template", action="store_true",
        help="Also generate a starter source file from a template.",
    )
    p_init.add_argument(
        "--lang", choices=["cpp", "java", "python"],
        help="Set language non-interactively.",
    )

    # ── 2. fetch ─────────────────────────────────────────────────────────
    p_fetch = sub.add_parser(
        "fetch",
        help="Fetch sample tests from Codeforces.",
        description="Download sample I/O from a CF problem.\n\n"
                    "Examples:\n"
                    "  kjudge fetch cf:1234A\n"
                    "  kjudge fetch https://codeforces.com/contest/1234/problem/A",
    )
    p_fetch.add_argument(
        "identifier",
        help="Problem identifier: 'cf:1234A' or a full Codeforces URL.",
    )

    # ── 3. add ───────────────────────────────────────────────────────────
    sub.add_parser(
        "add",
        help="Interactively add a custom test case.",
        description="Prompt for input and expected output, then save as custom_XXX.",
    )

    # ── 4. gen ───────────────────────────────────────────────────────────
    p_gen = sub.add_parser(
        "gen",
        help="Generate test inputs using an external command.",
        description="Run a generator command multiple times to create test inputs.\n\n"
                    "Example:\n"
                    "  kjudge gen --cmd \"python gen.py\" --count 50",
    )
    p_gen.add_argument("--cmd", required=True, help="Generator command to run.")
    p_gen.add_argument("--count", type=int, default=10,
                       help="Number of test inputs to generate (default: 10).")

    # ── 5. answer ────────────────────────────────────────────────────────
    p_answer = sub.add_parser(
        "answer",
        help="Fill missing .out files using a correct solution.",
        description="Run the solution on all .in files that lack a .out "
                    "and save the output as expected.",
    )
    _add_solution_arg(p_answer)
    p_answer.add_argument("--lang", choices=["cpp", "java", "python"],
                          help="Override language.")
    p_answer.add_argument("--time", type=int, metavar="MS",
                          help="Time limit in ms.")

    # ── 6. run ───────────────────────────────────────────────────────────
    p_run = sub.add_parser(
        "run",
        help="Run solution on all tests and show verdicts.",
        description="Compile (if needed) and run the solution on every test "
                    "case that has expected output.\n\n"
                    "Examples:\n"
                    "  kjudge run main.cpp --time 1000 --show-input\n"
                    "  kjudge run main.py --lang python --quiet",
    )
    _add_solution_arg(p_run)
    _add_run_options(p_run)

    # ── 7. case ──────────────────────────────────────────────────────────
    p_case = sub.add_parser(
        "case",
        help="Run a single test case.",
        description="Run the solution on one specific test.\n\n"
                    "Examples:\n"
                    "  kjudge case 3 main.cpp\n"
                    "  kjudge case sample_002 main.cpp",
    )
    p_case.add_argument("test_id", help="Test index (number) or name.")
    _add_solution_arg(p_case)
    _add_run_options(p_case)

    # ── 8. diff ──────────────────────────────────────────────────────────
    p_diff = sub.add_parser(
        "diff",
        help="Show colored diff between expected and actual output.",
        description="Display a side-by-side comparison for a test case.",
    )
    p_diff.add_argument("test_id", help="Test index (number) or name.")
    p_diff.add_argument("--show-input", action="store_true",
                        help="Also display the test input.")

    # ── 9. stress ────────────────────────────────────────────────────────
    p_stress = sub.add_parser(
        "stress",
        help="Stress test: find counterexample between two solutions.",
        description="Run a generator, feed input to both a brute-force and an "
                    "optimized solution, and find the first disagreement.\n\n"
                    "Example:\n"
                    "  kjudge stress --brute brute.cpp --smart main.cpp "
                    "--gen \"python gen.py\" --max 500",
    )
    p_stress.add_argument("--brute", required=True,
                          help="Brute-force (correct) solution file.")
    p_stress.add_argument("--smart", required=True,
                          help="Optimized solution file to test.")
    p_stress.add_argument("--gen", required=True,
                          help="Generator command (e.g. 'python gen.py').")
    p_stress.add_argument("--max", type=int, default=1000,
                          help="Max iterations (default: 1000).")
    p_stress.add_argument("--lang", choices=["cpp", "java", "python"],
                          help="Override language for both solutions.")
    p_stress.add_argument("--time", type=int, metavar="MS",
                          help="Time limit per run in ms.")

    # ── 10. watch ────────────────────────────────────────────────────────
    p_watch = sub.add_parser(
        "watch",
        help="Watch source file and auto-rerun tests on changes.",
        description="Poll-based file watcher that re-runs all tests "
                    "whenever the solution file is modified.",
    )
    _add_solution_arg(p_watch)
    p_watch.add_argument("--lang", choices=["cpp", "java", "python"],
                         help="Override language.")
    p_watch.add_argument("--time", type=int, metavar="MS",
                         help="Time limit in ms.")
    p_watch.add_argument("--interval", type=float, default=0.5,
                         help="Poll interval in seconds (default: 0.5).")

    # ── 11. contest ──────────────────────────────────────────────────────
    p_contest = sub.add_parser(
        "contest",
        help="Scaffold an entire contest (folders + init + fetch).",
        description="Create problem directories, init each, and fetch samples.\n\n"
                    "Examples:\n"
                    "  kjudge contest cf:1234 --problems A B C D E\n"
                    "  kjudge contest cf:1234   (auto-detect problems)",
    )
    p_contest.add_argument("identifier",
                           help="Contest identifier (e.g. 'cf:1234').")
    p_contest.add_argument("--problems", nargs="+", metavar="P",
                           help="Problem indices (e.g. A B C D). "
                                "If omitted, auto-detect from contest page.")
    p_contest.add_argument("--lang", choices=["cpp", "java", "python"],
                           help="Language for all problems.")
    p_contest.add_argument("--template", action="store_true",
                           help="Generate starter source files.")

    # ── 12. list ─────────────────────────────────────────────────────────
    sub.add_parser(
        "list",
        help="List all test cases in a table.",
        description="Show all test cases with status (has input, has output, size).",
    )

    # ── 13. clean ────────────────────────────────────────────────────────
    p_clean = sub.add_parser(
        "clean",
        help="Remove test cases or build artifacts.",
        description="Remove generated tests, custom tests, or everything.",
    )
    clean_group = p_clean.add_mutually_exclusive_group()
    clean_group.add_argument("--all", action="store_true",
                             help="Remove ALL tests and build artifacts.")
    clean_group.add_argument("--gen", action="store_true",
                             help="Remove only generated tests (gen_*).")
    clean_group.add_argument("--custom", action="store_true",
                             help="Remove only custom tests (custom_*).")
    clean_group.add_argument("--build", action="store_true",
                             help="Remove only build artifacts.")
    clean_group.add_argument("--samples", action="store_true",
                             help="Remove only sample tests (sample_*).")

    # ── 14. remove ───────────────────────────────────────────────────────
    p_remove = sub.add_parser(
        "remove",
        help="Delete a specific test case.",
        description="Remove both .in and .out files for a given test.",
    )
    p_remove.add_argument("test_id", help="Test index (number) or name.")

    # ── 15. export ───────────────────────────────────────────────────────
    p_export = sub.add_parser(
        "export",
        help="Export tests and config to a zip file.",
        description="Package all test cases and config into a zip.",
    )
    p_export.add_argument("output", nargs="?", default="kjudge_tests.zip",
                          help="Output zip filename (default: kjudge_tests.zip).")

    # ── 16. config ───────────────────────────────────────────────────────
    p_config = sub.add_parser(
        "config",
        help="View or edit global kjudge configuration.",
        description="Show or modify ~/.kjudge/config.json defaults.",
    )
    p_config.add_argument("--set", nargs=2, metavar=("KEY", "VALUE"),
                          action="append",
                          help="Set a config key (e.g. --set language cpp).")
    p_config.add_argument("--show", action="store_true",
                          help="Display current global config.")

    # ── 17. self-install ─────────────────────────────────────────────────
    sub.add_parser(
        "self-install",
        help="Install standalone executable to Windows PATH.",
    )

    # ── 18. self-uninstall ───────────────────────────────────────────────
    sub.add_parser(
        "self-uninstall",
        help="Deep uninstall of kjudge (removes PATH and ~/.kjudge).",
    )

    return parser


# ═══════════════════════════════════════════════════════════════════════════
# Command handlers (will be implemented in subsequent phases)
# ═══════════════════════════════════════════════════════════════════════════

def cmd_init(args):
    from kjudge.config import handle_init
    handle_init(args)

def cmd_fetch(args):
    from kjudge.cf_fetcher import handle_fetch
    handle_fetch(args)

def cmd_add(args):
    from kjudge.tests_store import handle_add
    handle_add(args)

def cmd_gen(args):
    from kjudge.runner import handle_gen
    handle_gen(args)

def cmd_answer(args):
    from kjudge.runner import handle_answer
    handle_answer(args)

def cmd_run(args):
    from kjudge.runner import handle_run
    handle_run(args)

def cmd_case(args):
    from kjudge.runner import handle_case
    handle_case(args)

def cmd_diff(args):
    from kjudge.diff_view import handle_diff
    handle_diff(args)

def cmd_stress(args):
    from kjudge.stress import handle_stress
    handle_stress(args)

def cmd_watch(args):
    from kjudge.watcher import handle_watch
    handle_watch(args)

def cmd_contest(args):
    from kjudge.contest import handle_contest
    handle_contest(args)

def cmd_list(args):
    from kjudge.tests_store import handle_list
    handle_list(args)

def cmd_clean(args):
    from kjudge.tests_store import handle_clean
    handle_clean(args)

def cmd_remove(args):
    from kjudge.tests_store import handle_remove
    handle_remove(args)

def cmd_export(args):
    from kjudge.exporter import handle_export
    handle_export(args)

def cmd_config(args):
    from kjudge.config import handle_config
    handle_config(args)

def cmd_self_install(args):
    from kjudge.setup_wizard import handle_self_install
    handle_self_install(args)

def cmd_self_uninstall(args):
    from kjudge.setup_wizard import handle_self_uninstall
    handle_self_uninstall(args)

# Map command names → handlers
HANDLERS = {
    "init": cmd_init,
    "fetch": cmd_fetch,
    "add": cmd_add,
    "gen": cmd_gen,
    "answer": cmd_answer,
    "run": cmd_run,
    "case": cmd_case,
    "diff": cmd_diff,
    "stress": cmd_stress,
    "watch": cmd_watch,
    "contest": cmd_contest,
    "list": cmd_list,
    "clean": cmd_clean,
    "remove": cmd_remove,
    "export": cmd_export,
    "config": cmd_config,
    "self-install": cmd_self_install,
    "self-uninstall": cmd_self_uninstall,
}


def main():
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    handler = HANDLERS.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    try:
        handler(args)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)
    except SystemExit:
        raise
    except Exception as e:
        from kjudge.utils import print_error
        print_error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
