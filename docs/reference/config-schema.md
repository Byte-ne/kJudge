# Configuration Schema

kJudge uses a tiered configuration system (Global -> Local) to maintain flexibility while reducing boilerplate for every problem.

## Local Config (`.kjudge/config.json`)

Created automatically by `kjudge init`. Controls behavior for a specific problem.

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `language` | `string` | `cpp` | The active language for the folder. |
| `time_limit_ms` | `integer` | `2000` | Max execution time per test case. |
| `memory_limit_mb` | `integer` | `256` | Max memory usage per test case. |
| `compile` | `string` | *varies* | The command used to compile the solution. |
| `run` | `string` | *varies* | The command used to execute the binary. |

## Global Config (`~/.kjudge/config.json`)

Used to set default values for all future `init` calls.

```bash
# Set global default language to python
kjudge config --set language python
```

## Custom Templates (`~/.kjudge/templates/`)

kJudge looks for templates in this folder during initialization:
- `main.cpp`
- `main.py`
- `Main.java`

You can customize these files to include your standard libraries, fast I/O code, or utility functions. Use `kjudge init --template` to apply them.

---

**See Also:**
- [CLI Reference](cli.md)
- [How-to: Setting up a Contest](../how-to/handle-contests.md)
