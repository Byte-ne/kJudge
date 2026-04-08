"""
exporter.py — Test case export/import for kjudge.

Packages test cases and config into a zip for sharing,
and supports importing from a zip.
"""

import os
import zipfile

from kjudge.utils import (
    KJUDGE_DIR, TESTS_DIR, CONFIG_FILE,
    find_kjudge_dir, console, print_success, print_error, print_info,
)


def handle_export(args):
    """Handle 'kjudge export' — zip tests + config."""
    base = find_kjudge_dir()
    output_path = args.output

    tests_dir = os.path.join(base, TESTS_DIR)
    config_path = os.path.join(base, CONFIG_FILE)

    if not os.path.isdir(tests_dir):
        print_error("No tests directory found.")
        return

    file_count = 0
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add config
        if os.path.exists(config_path):
            zf.write(config_path, "config.json")
            file_count += 1

        # Add all test files
        for f in sorted(os.listdir(tests_dir)):
            if f.endswith(".in") or f.endswith(".out"):
                full_path = os.path.join(tests_dir, f)
                zf.write(full_path, os.path.join("tests", f))
                file_count += 1

    size_kb = os.path.getsize(output_path) / 1024
    print_success(
        f"Exported {file_count} file(s) to [cyan]{output_path}[/] ({size_kb:.1f} KB)"
    )


def import_tests(zip_path: str, base_dir: str):
    """Import tests from a zip file into .kjudge/tests/."""
    tests_dir = os.path.join(base_dir, TESTS_DIR)
    os.makedirs(tests_dir, exist_ok=True)

    imported = 0
    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in zf.infolist():
            if info.filename.startswith("tests/"):
                name = os.path.basename(info.filename)
                if name and (name.endswith(".in") or name.endswith(".out")):
                    target = os.path.join(tests_dir, name)
                    with zf.open(info) as src, open(target, "wb") as dst:
                        dst.write(src.read())
                    imported += 1

    print_success(f"Imported {imported} file(s) from [cyan]{zip_path}[/]")
