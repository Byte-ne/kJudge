"""
config.py — Configuration management for kjudge.

Handles loading/saving both local (.kjudge/config.json) and
global (~/.kjudge/config.json) configs, with sensible defaults
for each supported language.
"""

import json
import os
import sys

from kjudge.utils import (
    KJUDGE_DIR, TESTS_DIR, LAST_RUN_DIR, CONFIG_FILE,
    GLOBAL_DIR, GLOBAL_CONFIG,
    ensure_kjudge_dir, console, print_success, print_info, print_error,
)


# ---------------------------------------------------------------------------
# Default configs per language
# ---------------------------------------------------------------------------
def get_defaults(language: str, main_file: str | None = None) -> dict:
    """Return sensible default config for a given language."""
    is_win = os.name == "nt"

    if language == "cpp":
        main_file = main_file or "main.cpp"
        exe = "main.exe" if is_win else "./main"
        return {
            "language": "cpp",
            "main_file": main_file,
            "build": f"g++ -std=c++17 -O2 -o {'main' if is_win else 'main'} {main_file}",
            "run": exe,
            "time_limit_ms": 2000,
            "memory_limit_mb": 256,
        }
    elif language == "java":
        main_file = main_file or "Main.java"
        return {
            "language": "java",
            "main_file": main_file,
            "build": f"javac {main_file}",
            "run": "java Main",
            "time_limit_ms": 3000,
            "memory_limit_mb": 256,
        }
    elif language == "python":
        main_file = main_file or "main.py"
        py = "python" if is_win else "python3"
        return {
            "language": "python",
            "main_file": main_file,
            "build": "",
            "run": f"{py} {main_file}",
            "time_limit_ms": 5000,
            "memory_limit_mb": 256,
        }
    else:
        print_error(f"Unknown language: {language}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Global config
# ---------------------------------------------------------------------------
def load_global_config() -> dict:
    """Load ~/.kjudge/config.json or return empty defaults."""
    if os.path.exists(GLOBAL_CONFIG):
        with open(GLOBAL_CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_global_config(data: dict):
    """Write global config to ~/.kjudge/config.json."""
    os.makedirs(GLOBAL_DIR, exist_ok=True)
    with open(GLOBAL_CONFIG, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


# ---------------------------------------------------------------------------
# Local config
# ---------------------------------------------------------------------------
def load_config(base_dir: str | None = None) -> dict:
    """
    Load .kjudge/config.json merged with global config.
    Local values override global.
    """
    base = base_dir or os.getcwd()
    config_path = os.path.join(base, CONFIG_FILE)
    global_cfg = load_global_config()

    if not os.path.exists(config_path):
        print_error(
            f"Config not found at {config_path}.\n"
            "  Run [bold]kjudge init[/] first."
        )
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        local_cfg = json.load(f)

    # Merge: local overrides global
    merged = {**global_cfg, **local_cfg}
    return merged


def save_config(base_dir: str, data: dict):
    """Write local config to .kjudge/config.json."""
    config_path = os.path.join(base_dir, CONFIG_FILE)
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def apply_overrides(config: dict, args) -> dict:
    """Apply CLI flag overrides (--lang, --time, --mem) to config."""
    config = dict(config)  # shallow copy

    if hasattr(args, "lang") and args.lang:
        defaults = get_defaults(args.lang)
        config["language"] = args.lang
        config["build"] = defaults["build"]
        config["run"] = defaults["run"]

    if hasattr(args, "time") and args.time:
        config["time_limit_ms"] = args.time

    if hasattr(args, "mem") and args.mem:
        config["memory_limit_mb"] = args.mem

    # If solution_file provided, update build/run accordingly
    if hasattr(args, "solution_file") and args.solution_file:
        lang = config.get("language", "cpp")
        sol = args.solution_file
        overrides = get_defaults(lang, sol)
        config["build"] = overrides["build"]
        config["run"] = overrides["run"]
        config["main_file"] = sol

    return config


# ---------------------------------------------------------------------------
# CLI handlers
# ---------------------------------------------------------------------------
def handle_init(args):
    """Handle 'kjudge init' — create .kjudge directory and config."""
    from rich.prompt import Prompt

    base = os.getcwd()
    kjudge_dir = os.path.join(base, KJUDGE_DIR)
    config_path = os.path.join(base, CONFIG_FILE)

    # Create directories
    ensure_kjudge_dir(base)

    if os.path.exists(config_path):
        print_info(f"Config already exists at [cyan]{config_path}[/]")
        console.print("  Use [bold]kjudge config[/] to modify settings.")
        return

    # Determine language
    global_cfg = load_global_config()
    if args.lang:
        language = args.lang
    elif "language" in global_cfg:
        language = global_cfg["language"]
        print_info(f"Using default language from global config: [bold]{language}[/]")
    else:
        language = Prompt.ask(
            "[bold]Select language[/]",
            choices=["cpp", "java", "python"],
            default="cpp",
        )

    # Get defaults
    defaults = get_defaults(language)

    # Ask for main file name
    if not args.lang:  # interactive mode
        main_file = Prompt.ask(
            "[bold]Main file name[/]",
            default=defaults["main_file"],
        )
        if main_file != defaults["main_file"]:
            defaults = get_defaults(language, main_file)

    # Save config
    save_config(base, defaults)

    print_success(f"Initialized kjudge in [cyan]{kjudge_dir}[/]")
    console.print(f"  Language: [bold]{language}[/]")
    console.print(f"  Build:    [dim]{defaults['build'] or '(none)'}[/]")
    console.print(f"  Run:      [dim]{defaults['run']}[/]")
    console.print(f"  Tests:    [dim]{os.path.join(base, TESTS_DIR)}[/]")

    # Optionally generate template
    if args.template:
        from kjudge.templates import generate_template
        generate_template(language, defaults["main_file"], base)


def handle_config(args):
    """Handle 'kjudge config' — view or edit global config."""
    from rich.syntax import Syntax

    if args.show or not args.set:
        # Show current global config
        cfg = load_global_config()
        if cfg:
            console.print("\n[bold]Global config[/] (~/.kjudge/config.json):\n")
            json_str = json.dumps(cfg, indent=2)
            console.print(Syntax(json_str, "json", theme="monokai"))
        else:
            print_info("No global config set. Use [bold]kjudge config --set KEY VALUE[/].")
        return

    if args.set:
        cfg = load_global_config()
        for key, value in args.set:
            # Try to parse as int/float/bool
            if value.lower() in ("true", "false"):
                value = value.lower() == "true"
            else:
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        pass
            cfg[key] = value
            print_success(f"Set [bold]{key}[/] = [cyan]{value}[/]")
        save_global_config(cfg)
