# kjudge — Competitive Programming Local Judge

A powerful CLI tool for competitive programming that manages test cases, fetches samples from Codeforces, compiles and runs solutions in C++/Java/Python, performs stress testing, and shows clear colored diffs.

## Installation

```bash
cd kJudge
pip install -e .
```

> **Windows note:** If `kjudge` isn't found after install, you may need to add the Python Scripts directory to your PATH, or use `python -m kjudge` instead.

## Quick Start

```bash
mkdir 1234A && cd 1234A
kjudge init                          # Set up problem directory
kjudge fetch cf:1234A                # Download sample tests from CF
# Write your solution in main.cpp
kjudge run main.cpp                  # Test against all samples
kjudge diff sample_002               # See colored diff for a failing test
kjudge case sample_002 main.cpp      # Re-run just that test
```

## Commands

### Core Workflow

| Command | Description |
|---|---|
| `kjudge init` | Initialize problem directory with `.kjudge/` config |
| `kjudge fetch cf:1234A` | Fetch sample tests from Codeforces |
| `kjudge add` | Interactively add a custom test case |
| `kjudge run main.cpp` | Run solution on all tests, show verdicts |
| `kjudge case 2 main.cpp` | Run a single test case |
| `kjudge diff sample_002` | Show colored diff between expected and actual |

### Test Generation & Regression

| Command | Description |
|---|---|
| `kjudge gen --cmd "python gen.py" --count 50` | Generate random test inputs |
| `kjudge answer main.cpp` | Fill missing `.out` files with correct solution |
| `kjudge stress --brute brute.cpp --smart main.cpp --gen "python gen.py"` | Find counterexamples |

### Contest Mode

| Command | Description |
|---|---|
| `kjudge contest cf:1234 --problems A B C D E` | Scaffold entire contest |
| `kjudge contest cf:1234` | Auto-detect problems from contest page |
| `kjudge contest cf:1234 --template` | Also generate starter source files |

### Test Management

| Command | Description |
|---|---|
| `kjudge list` | Show all test cases in a table |
| `kjudge remove sample_003` | Delete a specific test case |
| `kjudge clean --gen` | Remove generated tests |
| `kjudge clean --all` | Remove everything |
| `kjudge export` | Package tests into a zip file |

### Productivity

| Command | Description |
|---|---|
| `kjudge watch main.cpp` | Auto-rerun tests when file changes |
| `kjudge config --show` | View global configuration |
| `kjudge config --set language cpp` | Set global defaults |

### Advanced Options

```bash
# Custom checker for multi-answer problems
kjudge run main.cpp --checker "python checker.py"
kjudge run main.cpp --checker token          # Token-based comparison
kjudge run main.cpp --checker float:1e-6     # Float comparison

# Interactive problems
kjudge run main.cpp --interactive --checker interactor.py

# Override settings
kjudge run main.cpp --lang python --time 5000 --mem 512
kjudge run main.cpp --quiet                  # Summary only
kjudge run main.cpp --show-input --show-output
```

## Example Workflow

### Standard Problem

```bash
mkdir 1234A && cd 1234A
kjudge init                                    # → .kjudge/ created
kjudge fetch cf:1234A                          # → sample_001, sample_002
# edit main.cpp
kjudge run main.cpp                            # → AC/WA/TLE/RTE per test
kjudge diff sample_002                         # → see what went wrong
# fix bug
kjudge case sample_002 main.cpp                # → re-test single case
```

### Stress Testing

```bash
# After your solution passes samples:
kjudge gen --cmd "python gen_1234A.py" --count 50
kjudge answer main.cpp                         # Fill outputs with correct solution
kjudge run main.cpp                            # Regression test

# Or use stress directly:
kjudge stress --brute brute.cpp --smart main.cpp --gen "python gen.py" --max 500
```

### Full Contest

```bash
kjudge contest cf:2050 --problems A B C D E F --template --lang cpp
cd A
# solve...
kjudge run main.cpp
cd ../B
# ...
```