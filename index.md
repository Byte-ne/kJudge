---
layout: default
title: "kjudge - Competitive Programming CLI Local Judge"
---

# kjudge - Competitive Programming Local Judge

A powerful, command-line tool for competitive programming that manages test cases, fetches samples from Codeforces, compiles and runs solutions in C++/Java/Python, performs automatic stress testing, and shows clear diffs.

## Installation

Clone the repository and install it locally using pip:

```bash
cd kJudge
pip install -e .
```

*Note for Windows: If `kjudge` isn't found after taking this action, you may need to add the Python Scripts directory to your PATH, or use `python -m kjudge`.*

## Quick Start Example

The standard workflow for solving a Codeforces problem (e.g., 4A):

```bash
mkdir 4A && cd 4A
kjudge init                          # Set up problem directory
kjudge fetch cf:4A                   # Download sample tests from CF
# Write your solution in main.cpp...
kjudge run main.cpp                  # Test against all samples
kjudge diff sample_002               # See colored diff for a failing test
kjudge case sample_002 main.cpp      # Re-run just that test
```

## Commands Reference

| Command | Description |
|---|---|
| `kjudge init` | Initialize problem directory with `.kjudge/` config |
| `kjudge fetch cf:1234A` | Fetch sample test cases directly from Codeforces |
| `kjudge add` | Interactively add a custom test case |
| `kjudge run main.cpp` | Run solution on all tests, show verdicts (AC, WA, TLE, RTE) |
| `kjudge case 2 main.cpp` | Run a single test case by index or name |
| `kjudge diff sample_002` | Show a line-by-line diff comparing output vs expected |

### Test Generation & Regression

| Command | Description |
|---|---|
| `kjudge gen --cmd "python ..."` | Generate random test inputs using an external script |
| `kjudge answer main.cpp` | Fill missing `.out` files with a correct solution |
| `kjudge stress --brute ...` | Stress testing: find counterexamples automatically |

### Contest Mode

| Command | Description |
|---|---|
| `kjudge contest cf:1234` | Scaffold an entire contest globally (Downloads all A B C problems) |

## Platform Architecture & Deep Dives

For contributors and advanced users, the underlying mechanics of `kjudge` are extensively documented. These files discuss the engineering choices from sub-process pipe isolations to our polyglot target-compilation engine:

- [Platform Architecture & Internals](/docs/architecture.html) - OS level daemon threads, process bounding, state architectures.
- [Advanced Verification Workflows](/docs/advanced_workflows.html) - Automated N-loop stress engines, custom AST-level checkers, and our internal polling watcher logic.
- [Config Parsing & Mechanics](/docs/config_mechanics.html) - JSON overlay priority hierarchy and dynamic target selection.
- [Distribution & Standalone Setup](/docs/distribution.html) - Replicating, PyPI PIP installations, and deploying explicit standalone `.exe` binaries using PyInstaller.

