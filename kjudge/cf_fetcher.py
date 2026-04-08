"""
cf_fetcher.py — Codeforces sample test scraper for kjudge.

Fetches sample input/output pairs from Codeforces problem pages
by parsing the HTML structure.
"""

import re
import sys

import requests
from bs4 import BeautifulSoup

from kjudge.utils import (
    find_kjudge_dir, normalize_output,
    console, print_success, print_error, print_info,
)
from kjudge.tests_store import save_test, get_next_index


# ---------------------------------------------------------------------------
# Parsing identifiers
# ---------------------------------------------------------------------------
def parse_cf_identifier(identifier: str) -> tuple[str, str]:
    """
    Parse a Codeforces problem identifier into (contest_id, problem_index).

    Accepts:
      - "cf:1234A" or "cf:1234/A"
      - "1234A"
      - "https://codeforces.com/contest/1234/problem/A"
      - "https://codeforces.com/problemset/problem/1234/A"
      - "https://codeforces.com/gym/1234/problem/A"
    """
    identifier = identifier.strip()

    # Strip "cf:" prefix
    if identifier.lower().startswith("cf:"):
        identifier = identifier[3:]

    # URL patterns
    url_patterns = [
        r"codeforces\.com/contest/(\d+)/problem/([A-Za-z]\d?)",
        r"codeforces\.com/problemset/problem/(\d+)/([A-Za-z]\d?)",
        r"codeforces\.com/gym/(\d+)/problem/([A-Za-z]\d?)",
    ]
    for pattern in url_patterns:
        match = re.search(pattern, identifier)
        if match:
            return match.group(1), match.group(2).upper()

    # "1234/A" format
    match = re.match(r"^(\d+)/([A-Za-z]\d?)$", identifier)
    if match:
        return match.group(1), match.group(2).upper()

    # "1234A" or "1234A1" format
    match = re.match(r"^(\d+)([A-Za-z]\d?)$", identifier)
    if match:
        return match.group(1), match.group(2).upper()

    print_error(
        f"Cannot parse identifier: '{identifier}'\n"
        "  Expected: cf:1234A, 1234A, or a Codeforces URL."
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Fetching samples
# ---------------------------------------------------------------------------
def fetch_samples(contest_id: str, problem_index: str) -> list[tuple[str, str]]:
    """
    Fetch sample input/output pairs from a Codeforces problem page.
    Returns list of (input_str, output_str) pairs.
    """
    url = f"https://codeforces.com/contest/{contest_id}/problem/{problem_index}"

    console.print(f"[dim]Fetching: {url}[/]")

    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "kjudge/1.0 (competitive-programming-judge)",
        })
        resp.raise_for_status()
    except requests.RequestException as e:
        print_error(f"Failed to fetch problem page: {e}")
        sys.exit(1)

    soup = BeautifulSoup(resp.text, "html.parser")

    # Find the sample test section
    sample_tests = soup.find("div", class_="sample-test")
    if not sample_tests:
        # Try alternative structure
        sample_tests = soup.find("div", class_="sample-tests")

    if not sample_tests:
        print_error(
            "Could not find sample tests on the page.\n"
            "  The problem page structure may have changed, "
            "or the problem ID may be incorrect."
        )
        sys.exit(1)

    # Extract input/output pairs
    inputs = sample_tests.find_all("div", class_="input")
    outputs = sample_tests.find_all("div", class_="output")

    if len(inputs) != len(outputs):
        print_error(
            f"Mismatched sample counts: {len(inputs)} inputs vs {len(outputs)} outputs.\n"
            "  The page structure may be unexpected."
        )
        sys.exit(1)

    if not inputs:
        print_error("No sample tests found on the page.")
        sys.exit(1)

    pairs = []
    for inp_div, out_div in zip(inputs, outputs):
        # Extract text from <pre> blocks
        inp_pre = inp_div.find("pre")
        out_pre = out_div.find("pre")

        if inp_pre is None or out_pre is None:
            continue

        # Handle <br/> tags in pre blocks (CF sometimes uses these)
        input_text = _extract_pre_text(inp_pre)
        output_text = _extract_pre_text(out_pre)

        # Normalize
        input_text = _normalize_sample(input_text)
        output_text = _normalize_sample(output_text)

        pairs.append((input_text, output_text))

    return pairs


def _extract_pre_text(pre_tag) -> str:
    """
    Extract text from a <pre> tag that may contain <br/> tags
    or nested <div> elements (CF uses various formats).
    """
    # Check for <div class="test-example-line"> children (newer CF format)
    lines = pre_tag.find_all("div", class_="test-example-line")
    if lines:
        return "\n".join(line.get_text() for line in lines)

    # Replace <br> with newlines
    for br in pre_tag.find_all("br"):
        br.replace_with("\n")

    return pre_tag.get_text()


def _normalize_sample(text: str) -> str:
    """Normalize a sample text: fix line endings, strip trailing whitespace."""
    text = text.replace("\r\n", "\n")
    lines = text.split("\n")
    lines = [line.rstrip() for line in lines]

    # Strip leading/trailing empty lines
    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Fetching contest problem list
# ---------------------------------------------------------------------------
def fetch_contest_problems(contest_id: str) -> list[str]:
    """
    Scrape the contest page to find all problem indices (A, B, C, ...).
    """
    url = f"https://codeforces.com/contest/{contest_id}"

    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "kjudge/1.0 (competitive-programming-judge)",
        })
        resp.raise_for_status()
    except requests.RequestException as e:
        print_error(f"Failed to fetch contest page: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # Find problem links in the problems table
    problems = []
    table = soup.find("table", class_="problems")
    if table:
        for row in table.find_all("tr"):
            td = row.find("td", class_="id")
            if td:
                link = td.find("a")
                if link:
                    idx = link.get_text().strip().upper()
                    if idx:
                        problems.append(idx)

    return problems


# ---------------------------------------------------------------------------
# CLI handler
# ---------------------------------------------------------------------------
def handle_fetch(args):
    """Handle 'kjudge fetch' — download sample tests from Codeforces."""
    base = find_kjudge_dir()
    contest_id, problem_index = parse_cf_identifier(args.identifier)

    console.print(
        f"\n[bold]Fetching samples for problem[/] "
        f"[cyan]{contest_id}{problem_index}[/]\n"
    )

    pairs = fetch_samples(contest_id, problem_index)

    for i, (inp, out) in enumerate(pairs, 1):
        idx = get_next_index(base, "sample")
        name = f"sample_{idx:03d}"
        save_test(base, name, inp, out)

    print_success(f"Fetched [bold]{len(pairs)}[/] sample test(s)")
