"""
checker.py — Custom checker support for kjudge.

Supports external checker scripts and built-in checkers
(token-based, floating-point) for problems with multiple valid outputs.
"""

import os
import subprocess
import tempfile

from kjudge.utils import AC, WA, print_error


def run_checker(
    checker_cmd: str,
    input_str: str,
    expected_str: str,
    actual_str: str,
) -> str:
    """
    Run a checker and return AC or WA.

    Built-in checkers:
      - "token"       — compare token-by-token ignoring whitespace
      - "float:1e-6"  — compare floating-point values with epsilon

    External checker:
      - Receives (input_file, expected_file, actual_file) as args
      - Exit 0 = AC, non-zero = WA
    """
    # Built-in: token checker
    if checker_cmd.strip().lower() == "token":
        return _check_tokens(expected_str, actual_str)

    # Built-in: float checker
    if checker_cmd.strip().lower().startswith("float"):
        parts = checker_cmd.split(":")
        eps = float(parts[1]) if len(parts) > 1 else 1e-6
        return _check_float(expected_str, actual_str, eps)

    # External checker
    return _run_external_checker(checker_cmd, input_str, expected_str, actual_str)


def _check_tokens(expected: str, actual: str) -> str:
    """Compare token-by-token, ignoring all whitespace differences."""
    exp_tokens = expected.split()
    act_tokens = actual.split()

    if exp_tokens == act_tokens:
        return AC
    return WA


def _check_float(expected: str, actual: str, epsilon: float) -> str:
    """Compare floating-point numbers with epsilon tolerance."""
    exp_tokens = expected.split()
    act_tokens = actual.split()

    if len(exp_tokens) != len(act_tokens):
        return WA

    for e, a in zip(exp_tokens, act_tokens):
        try:
            ef = float(e)
            af = float(a)
            if abs(ef - af) > epsilon and abs(ef - af) > epsilon * max(abs(ef), 1.0):
                return WA
        except ValueError:
            # Not a number, compare as string
            if e != a:
                return WA

    return AC


def _run_external_checker(
    checker_cmd: str,
    input_str: str,
    expected_str: str,
    actual_str: str,
) -> str:
    """
    Run an external checker program.
    The checker receives three temp files as arguments:
      checker_cmd input_file expected_file actual_file
    Exit 0 = AC, non-zero = WA.
    """
    try:
        # Write temp files
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".in", delete=False, encoding="utf-8"
        ) as f_in:
            f_in.write(input_str)
            in_path = f_in.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".expected", delete=False, encoding="utf-8"
        ) as f_exp:
            f_exp.write(expected_str)
            exp_path = f_exp.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".actual", delete=False, encoding="utf-8"
        ) as f_act:
            f_act.write(actual_str)
            act_path = f_act.name

        # Run checker
        full_cmd = f'{checker_cmd} "{in_path}" "{exp_path}" "{act_path}"'
        result = subprocess.run(
            full_cmd, shell=True, capture_output=True, text=True, timeout=10,
        )

        return AC if result.returncode == 0 else WA

    except subprocess.TimeoutExpired:
        print_error("Checker timed out (10s limit)")
        return WA
    except Exception as e:
        print_error(f"Checker error: {e}")
        return WA
    finally:
        # Clean up temp files
        for path in [in_path, exp_path, act_path]:
            try:
                os.remove(path)
            except OSError:
                pass
