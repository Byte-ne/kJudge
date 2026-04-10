# CLI Command Reference

This is a comprehensive reference for all `kjudge` commands and their options.

## Core Commands

### `init`
Initialize a kJudge problem directory.
```bash
kjudge init [--lang LANG] [--template]
```
- `--lang`: Language of the starter file (`cpp`, `java`, `python`).
- `--template`: If set, uses your custom template from `~/.kjudge/templates/`.

### `run`
Compile and run a solution against all local test cases.
```bash
kjudge run [FILE]
```
- `FILE`: The source code file to run (default: auto-detected).

### `list`
List all test cases in the current directory.
```bash
kjudge list [--verbose]
```

### `add`
Interactively add a new test case.
```bash
kjudge add [--sample] [--name NAME]
```

## Advanced Commands

### `fetch`
Download samples from Codeforces.
```bash
kjudge fetch IDENTIFIER
```
- `IDENTIFIER`: Problem ID (e.g., `4A`, `cf:1234B`, or a full URL).

### `contest`
Scaffold an entire Codeforces contest.
```bash
kjudge contest IDENTIFIER [--problems A B C...]
```

### `config`
Manage global and local configuration.
```bash
kjudge config [--show] [--set KEY VALUE]
```

### `export`
Export all local test cases to a zip file.
```bash
kjudge export [FILENAME]
```

### `clean`
Remove temporary compilation artifacts and the `.kjudge` metadata folder.
```bash
kjudge clean [--all]
```

---

**See Also:**
- [Configuration Schema](docs/reference/config-schema.md)
- [How-to: Handle Contests](../how-to/handle-contests.md)
