"""
templates.py — Code template management for kjudge.

Provides default starter source files for C++, Java, and Python,
and supports user-defined custom templates from ~/.kjudge/templates/.
"""

import os

from kjudge.utils import TEMPLATES_DIR, print_success, print_info


# ---------------------------------------------------------------------------
# Default templates
# ---------------------------------------------------------------------------
CPP_TEMPLATE = """\
#include <bits/stdc++.h>
using namespace std;

#define ll long long
#define pb push_back
#define all(x) (x).begin(), (x).end()
#define sz(x) (int)(x).size()

void solve() {
    // TODO: your solution here
}

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(nullptr);

    int t = 1;
    // cin >> t;
    while (t--) solve();

    return 0;
}
"""

JAVA_TEMPLATE = """\
import java.util.*;
import java.io.*;

public class Main {
    public static void main(String[] args) throws Exception {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        StringBuilder sb = new StringBuilder();

        // TODO: your solution here

        System.out.print(sb);
    }
}
"""

PYTHON_TEMPLATE = """\
import sys
input = sys.stdin.readline

def solve():
    # TODO: your solution here
    pass

def main():
    t = 1
    # t = int(input())
    for _ in range(t):
        solve()

if __name__ == "__main__":
    main()
"""

DEFAULT_TEMPLATES = {
    "cpp": CPP_TEMPLATE,
    "java": JAVA_TEMPLATE,
    "python": PYTHON_TEMPLATE,
}


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------
def load_custom_template(language: str) -> str | None:
    """
    Load a custom template from ~/.kjudge/templates/ if it exists.
    Expected filenames: main.cpp, Main.java, main.py
    """
    filename_map = {
        "cpp": "main.cpp",
        "java": "Main.java",
        "python": "main.py",
    }
    filename = filename_map.get(language)
    if not filename:
        return None

    path = os.path.join(TEMPLATES_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return None


def get_template(language: str) -> str:
    """
    Get the template for a language.
    Prefers custom templates over defaults.
    """
    custom = load_custom_template(language)
    if custom is not None:
        return custom
    return DEFAULT_TEMPLATES.get(language, "")


def generate_template(language: str, main_file: str, base_dir: str):
    """Write a starter source file to the problem directory."""
    filepath = os.path.join(base_dir, main_file)

    if os.path.exists(filepath):
        print_info(f"[cyan]{main_file}[/] already exists, skipping template generation.")
        return

    template = get_template(language)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(template)

    print_success(f"Created template [cyan]{main_file}[/]")
