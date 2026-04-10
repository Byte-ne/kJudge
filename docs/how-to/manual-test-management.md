# Manual Test Management

For problems on private judges or when automated fetchers are blocked, you can manage test cases manually using kJudge's built-in tools.

## Adding Tests

The `add` command provides an interactive way to input test cases.

```bash
kjudge add
```

- When prompted for **Input**, paste the data and end with `Ctrl+Z` (Windows) or `Ctrl+D` (Linux/Mac).
- When prompted for **Output**, do the same.

## Managing the Test Store

kJudge stores test cases in `.kjudge/tests/` as simple text files:
- `test_001.in` / `test_001.out`
- `sample_001.in` / `sample_001.out`

You can manually edit these files using any text editor. kJudge will pick up any file with a `.in` extension and look for a matching `.out` file.

## Listing Tests

To see all test cases currently registered in the folder:

```bash
kjudge list
```

## Exporting for Submission

If you need to share your test cases or use them in another tool, use the `export` command to gather them into a single zip file:

```bash
kjudge export my_tests.zip
```

---

**See Also:**
- [CLI Reference](../reference/cli.md)
- [Explanation: Isolation Model](../explanation/architecture.md)
