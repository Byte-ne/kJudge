# Architecture & Design

kJudge is built on the principles of **minimality**, **isolation**, and **correctness**. This page explains the internal mechanisms that make it reliable for local judging.

## 1. Isolation Model

kJudge executes your code in a managed subprocess. While it doesn't use heavy containerization (like Docker), it applies several layers of isolation:

- **Time Isolation**: Precise monitoring of execution time, with automatic `TerminateProcess` calls if the time limit is exceeded.
- **Memory Tracking**: (Experimental) Monitoring of the child process memory tree to detect memory limit violations.
- **Directory Isolation**: All metadata and test data are stored in a hidden `.kjudge` folder, keeping your workspace clean.

## 2. Verdiction Logic

When you run `kjudge run`, each test case goes through the following states:

1.  **PENDING**: Waiting to be run.
2.  **RUNNING**: Code is currently executing.
3.  **COMPLETED**: Process exited naturally.
4.  **TLE**: Process was terminated for exceeding the time limit.
5.  **RTE**: Process crashed (non-zero exit code).

If **COMPLETED**, kJudge performs a **Token-based comparison**:
- Trailing whitespace is ignored on every line.
- Empty lines at the end of the output are ignored.
- Only non-matching tokens trigger a **Wrong Answer (WA)**.

## 3. Storage Architecture

kJudge uses a flat-file storage system for maximum transparency:

```text
.kjudge/
├── config.json       (Local settings)
├── tests/            (Test case pairs)
│   ├── sample_001.in
│   ├── sample_001.out
│   ├── test_001.in
│   └── test_001.out
└── .cache/           (Temporary binaries)
```

This structure makes it easy to debug tests or export them to other systems.

---

**See Also:**
- [CLI Reference](../reference/cli.md)
- [How-to: Manual Test Management](../how-to/manual-test-management.md)
