"""
cf_fetcher.py — Robust Codeforces sample test scraper for kjudge.

Uses a multi-source approach to ensure samples are fetched "at any cost":
1. Direct Codeforces fetch via curl_cffi (TLS fingerprinting bypass).
2. Fallback to VJudge with internal ID extraction and description scraping.
"""

import re
import sys
import time
import requests
from bs4 import BeautifulSoup

try:
    from curl_cffi import requests as curlit
except ImportError:
    curlit = None

from kjudge.utils import (
    find_kjudge_dir, normalize_output,
    console, print_success, print_error, print_info, WARNING_ICON,
)
from kjudge.tests_store import save_test, get_next_index


# ---------------------------------------------------------------------------
# Parsing identifiers
# ---------------------------------------------------------------------------
def parse_cf_identifier(identifier: str) -> tuple[str, str]:
    """Parse a Codeforces problem identifier into (contest_id, problem_index)."""
    identifier = identifier.strip()
    if identifier.lower().startswith("cf:"):
        identifier = identifier[3:]

    url_patterns = [
        r"codeforces\.com/contest/(\d+)/problem/([A-Za-z]\d?)",
        r"codeforces\.com/problemset/problem/(\d+)/([A-Za-z]\d?)",
        r"codeforces\.com/gym/(\d+)/problem/([A-Za-z]\d?)",
    ]
    for pattern in url_patterns:
        match = re.search(pattern, identifier)
        if match:
            return match.group(1), match.group(2).upper()

    match = re.match(r"^(\d+)/([A-Za-z]\d?)$", identifier)
    if match:
        return match.group(1), match.group(2).upper()

    match = re.match(r"^(\d+)([A-Za-z]\d?)$", identifier)
    if match:
        return match.group(1), match.group(2).upper()

    print_error(f"Cannot parse identifier: '{identifier}'. Use cf:1234A format.")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Core Fetching Logic
# ---------------------------------------------------------------------------
def fetch_samples(contest_id: str, problem_index: str) -> list[tuple[str, str]]:
    """Fetch samples with multi-source fallback."""
    problem_index = problem_index.upper()
    
    # 1. Attempt Codeforces Direct (curl_cffi)
    samples = _fetch_cf_direct(contest_id, problem_index)
    if samples:
        return samples

    # 2. Attempt Codeforces Desktop Mirror
    # (Sometimes hitting /contest/ instead of /problemset/ works)
    samples = _fetch_cf_contest_page(contest_id, problem_index)
    if samples:
        return samples

    # 3. Fallback to VJudge (Reliable mirror)
    print_info("Codeforces blocked the fetch. Attempting fallback via VJudge mirror...")
    return _fetch_vjudge_fallback(contest_id, problem_index)


def _fetch_cf_direct(contest_id: str, problem_index: str) -> list[tuple[str, str]]:
    """Primary fetch from Codeforces using curl_cffi."""
    url = f"https://codeforces.com/problemset/problem/{contest_id}/{problem_index}"
    return _cf_request_and_parse(url, "Direct")

def _fetch_cf_contest_page(contest_id: str, problem_index: str) -> list[tuple[str, str]]:
    """Secondary fetch from the contest problem page."""
    url = f"https://codeforces.com/contest/{contest_id}/problem/{problem_index}"
    return _cf_request_and_parse(url, "Contest Page")

def _cf_request_and_parse(url: str, label: str) -> list[tuple[str, str]]:
    console.print(f"[dim]Attempting {label}: {url}[/]")
    try:
        html = ""
        if curlit:
            # Impersonate modern Chrome to bypass TLS fingerprinting blocks
            resp = curlit.get(url, impersonate="chrome110", timeout=15)
            if resp.status_code == 200:
                html = resp.text
        else:
            import cloudscraper
            scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
            resp = scraper.get(url, timeout=15)
            if resp.status_code == 200:
                html = resp.text
        
        if html:
            return _parse_standard_cf_html(html)
    except Exception as e:
        console.print(f"[dim]Codeforces {label} failed: {e}[/]")
    return []


def _fetch_vjudge_fallback(contest_id: str, problem_index: str) -> list[tuple[str, str]]:
    """Robust VJudge mirror fetch."""
    v_id = f"Codeforces-{contest_id}{problem_index}"
    url = f"https://vjudge.net/problem/{v_id}"
    console.print(f"[dim]Mirroring: {url}[/]")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://vjudge.net/",
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        
        # VJudge loads the description via AJAX. We need the internal ID.
        # Find it in the dataJson block
        match = re.search(r'problemId":\s*(\d+)', resp.text)
        html = resp.text
        if match:
            internal_id = match.group(1)
            desc_url = f"https://vjudge.net/description/{internal_id}"
            # Important: VJudge description fragments are often returned on their own
            desc_resp = requests.get(desc_url, headers={"User-Agent": headers["User-Agent"], "Referer": url}, timeout=15)
            if desc_resp.status_code == 200:
                html = desc_resp.text
            else:
                # Try the alternate viewProblemDes
                desc_url = f"https://vjudge.net/problem/viewProblemDes/{internal_id}"
                desc_resp = requests.get(desc_url, headers={"User-Agent": headers["User-Agent"], "Referer": url}, timeout=15)
                if desc_resp.status_code == 200:
                    html = desc_resp.text

        return _parse_generic_html(html)
    except Exception as e:
        print_error(f"Mirror fallback failed: {e}")
    return []


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------
def _parse_standard_cf_html(html: str) -> list[tuple[str, str]]:
    """Parse samples from standard Codeforces problem HTML."""
    soup = BeautifulSoup(html, "html.parser")
    sample_test = soup.find("div", class_=re.compile(r"sample-tests?"))
    if not sample_test: return []

    inputs = sample_test.find_all("div", class_="input")
    outputs = sample_test.find_all("div", class_="output")

    pairs = []
    for inp_div, out_div in zip(inputs, outputs):
        inp_pre = inp_div.find("pre")
        out_pre = out_div.find("pre")
        if inp_pre and out_pre:
            input_text = _extract_pre_text(inp_pre)
            output_text = _extract_pre_text(out_pre)
            pairs.append((_normalize_sample(input_text), _normalize_sample(output_text)))
    return pairs


def _parse_generic_html(html: str) -> list[tuple[str, str]]:
    """Performs a broad search for samples in mirror sites."""
    # First check if it's mirroring CF's structure
    results = _parse_standard_cf_html(html)
    if results: return results

    # Broad scan for Sample Input/Output headers
    soup = BeautifulSoup(html, "html.parser")
    results = []
    
    # Identify headers that look like "Sample Input"
    for header in soup.find_all(["h4", "p", "div", "b", "strong", "h2"]):
        text = header.get_text().strip().lower()
        if "sample input" in text or "example input" in text:
            inp_pre = header.find_next(["pre", "div", "code"])
            if not inp_pre: continue
                
            # Search for corresponding output header
            out_pre = None
            curr = inp_pre.find_next(["h4", "p", "div", "b", "strong", "h2"])
            limit = 0
            while curr and limit < 5:
                h_text = curr.get_text().lower()
                if "sample output" in h_text or "example output" in h_text:
                    out_pre = curr.find_next(["pre", "div", "code"])
                    break
                curr = curr.find_next(["h4", "p", "div", "b", "strong", "h2"])
                limit += 1

            if inp_pre and out_pre:
                results.append((
                    _normalize_sample(inp_pre.get_text()),
                    _normalize_sample(out_pre.get_text())
                ))
    
    return results


def _extract_pre_text(pre_tag) -> str:
    """Extract text from a <pre> tag, handling CF's nested div structure."""
    lines = pre_tag.find_all("div", class_="test-example-line")
    if lines:
        return "\n".join(line.get_text() for line in lines)
    for br in pre_tag.find_all("br"):
        br.replace_with("\n")
    return pre_tag.get_text()


def _normalize_sample(text: str) -> str:
    """Cleanup sample text."""
    text = text.replace("\r\n", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    while lines and not lines[0].strip(): lines.pop(0)
    while lines and not lines[-1].strip(): lines.pop()
    return "\n".join(lines) + "\n" if lines else ""


# ---------------------------------------------------------------------------
# Contest Logic & CLI
# ---------------------------------------------------------------------------
def fetch_contest_problems(contest_id: str) -> list[str]:
    """Find all problem indices in a contest."""
    url = f"https://codeforces.com/contest/{contest_id}"
    try:
        resp = None
        if curlit:
            resp = curlit.get(url, impersonate="chrome110", timeout=15)
        else:
            import cloudscraper
            scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
            resp = scraper.get(url, timeout=15)
        
        if resp and resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            table = soup.find("table", class_="problems")
            if table:
                problems = []
                for row in table.find_all("tr"):
                    td = row.find("td", class_="id")
                    if td and (link := td.find("a")):
                        problems.append(link.get_text().strip().upper())
                return problems
    except: pass
    return ["A", "B", "C", "D", "E"]


def handle_fetch(args):
    """Entry point for kjudge fetch."""
    base = find_kjudge_dir()
    contest_id, problem_index = parse_cf_identifier(args.identifier)
    console.print(f"\n[bold]Fetching samples for[/] [cyan]{contest_id}{problem_index}[/]\n")

    pairs = fetch_samples(contest_id, problem_index)
    if not pairs:
        print_error("Failed to fetch samples automatically. Codeforces bot protection is currently very strong.")
        print_info("TIP: Use 'kjudge add' to manually paste test cases from your browser.")
        sys.exit(1)

    for i, (inp, out) in enumerate(pairs, 1):
        idx = get_next_index(base, "sample")
        save_test(base, f"sample_{idx:03d}", inp, out)

    print_success(f"Successfully fetched [bold]{len(pairs)}[/] sample test(s)")
