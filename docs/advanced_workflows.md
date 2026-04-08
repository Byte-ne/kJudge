

# Advanced Verification Workflows

Documentation on utilizing automated verification methodologies.

## 1. Automated Stress Testing Theory

Finding edge cases manually is sub-optimal. The `kjudge stress` heuristic operates on an `N`-loop generator pattern designed to crash the `smart` program before the `brute-force` baseline program finishes.

**Execution Flow Pipeline:**
1. A python-based or binary random input generator is fired, its payload captured in `stdout`.
2. The `brute` solution executes. If the `brute` triggers an RTE or TLE, `kjudge` marks the payload as invalid, skipping downstream execution.
3. The `smart` solution handles the payload.
4. An aggressive line-by-line whitespace-agnostic traversal runs. On `WA` or anomaly, execution halters, and the inputs are serialized to an artifact named `stress_XXX`.

## 2. Granular AST-Level Checkers

Multi-answer problems (e.g. "print any graph that...") require dynamic verification logic.

`kjudge` exposes an abstracted validator pipeline via the `--checker` flag. A custom checker executes on a secondary fork with exact file paths exposed via positional arguments (`sys.argv[1]`, `sys.argv[2]`, `sys.argv[3]`).

For mathematical thresholds, the built-in floating point comparator utilizes relative scalar error correction:
```python
# Absolute scalar difference
abs(expected - actual) > epsilon 
# Relative scalar threshold correction
and abs(expected - actual) > epsilon * max(abs(expected), 1.0)
```
This protects against floating point precision degradation scaling errors common in `O(N^2)` geometric calculations.

## 3. High-Velocity Watch Mode

The polling algorithm for `--watch` skips expensive `watchdog` bindings and OS-specific kernel traps (`inotify` vs `FSEvents`). It utilizes a `0.5s` polling loop on `os.path.getmtime(filepath)` which is cheap on memory and fully agnostic across Win32/POSIX substrates.

Upon a triggered differential, it implements an optimized clean-rebuild-execute DAG structure natively.
