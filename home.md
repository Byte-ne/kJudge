# kJudge ($kilo Judge$)
## A Local CP Judge
<img src="/true_logo.png" align = "center" width="200" height="200"> 

A powerful, command-line tool for competitive programming that manages test cases, fetches samples from Codeforces, compiles and runs solutions in C++/Java/Python, performs automatic stress testing, and shows clear diffs.

## Installation

Goto [github releases](https://github.com/Byte-ne/kJudge/releases) and install the **kjudge.exe** excecutable given. 

After running, a terminal will open as follows:

```bash
⚡ Welcome to the kjudge CLI Setup ⚡                         
                                                            
It looks like you opened the standalone executable directly.               
Would you like to permanently install kjudge to your system?
This will copy it to C:\Users\their_name\.kjudge\bin and add it to your PATH.
Install kjudge? (Y/n):
```

*What does Y do?* $-$
- amends PATH for global usage of kJudge
- copies iself into a permanent hidden folder (immutable), $ie.$ **~/.kjudge**

After this, all commands of kjudge will become avialable to the user, beginning with prefix **kjudge**.

*Note for Windows: If `kjudge` isn't found after taking this action, you may need to refresh your terminal as windows updates PATH on new terminals*

## Un-Installation

The un-installation process for kJudge is quite straightforward, just run 

```bash
kjudge self-uninstall #deletes all files associated with kJudge
# this also deletes all the templates made with kJudge, kindly gather backups
```

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

## Configuration

### Local Config (`.kjudge/config.json`)

```json
{
  "language": "cpp",
  "main_file": "main.cpp",
  "build": "g++ -std=c++17 -O2 -o main main.cpp",
  "run": "main.exe",
  "time_limit_ms": 2000,
  "memory_limit_mb": 256
}
```

### Global Config (`~/.kjudge/config.json`)

Set defaults that apply to all problems:

```bash
kjudge config --set language cpp
kjudge config --set time_limit_ms 3000
kjudge config --show
```

### Custom Templates (`~/.kjudge/templates/`)

Place your starter files in `~/.kjudge/templates/`:
- `main.cpp` — C++ template
- `Main.java` — Java template
- `main.py` — Python template

These are used by `kjudge init --template` and `kjudge contest --template`.

## Verdict Colors

| Verdict | Meaning | Color |
|---|---|---|
| **AC** | Accepted | ![text](https://img.shields.io/badge/AC-green) |
| **WA** | Wrong Answer | ![text](https://img.shields.io/badge/WA-red) |
| **TLE** | Time Limit Exceeded | ![text](https://img.shields.io/badge/TLE-yellow) |
| **RTE** | Runtime Error | ![text](https://img.shields.io/badge/RTE-purple) |

## License

[MIT](LICENSE.md)