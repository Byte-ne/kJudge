# Handling Contests with kJudge

kJudge includes specialized tools for competitive programmers participating in live contests, especially on **Codeforces**.

## 1. Scaffolding a Contest

If you want to prepare an entire contest locally, use the `contest` command. This will create a folder for the contest and subfolders for each problem (A, B, C, etc.).

```bash
# General usage
kjudge contest cf:1234

# Specify problems manually if the automatic fetcher is blocked
kjudge contest cf:1234 --problems A B C D E
```

This creates a directory `contest_1234/` with pre-initialized problem folders.

## 2. Fetching Samples Automatically

kJudge attempts to scrape sample test cases directly from Codeforces.

```bash
# Inside a problem directory
kjudge fetch cf:1234A
```

**NOTE**:
> Codeforces uses aggressive bot protection (Cloudflare). If `fetch` fails, kJudge will attempt a fallback via VJudge. If both fail, you will be prompted to add samples manually.

## 3. Automated Setup Wizard

For new installations, use the `self-install` command to automatically configure your binary location and verify your local environment.

```bash
kjudge self-install
```

---

**See Also:**
- [Manual Test Management](manual-test-management.md)
- [CLI Reference](../reference/cli.md)
