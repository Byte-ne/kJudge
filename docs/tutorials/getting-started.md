# Getting Started with kJudge

Welcome to **kJudge**, your minimalist command-line companion for competitive programming. This tutorial will take you from zero to running your first problem in under 5 minutes.

## 1. Installation

kJudge is distributed as a single standalone executable.

1.  Download `kjudge.exe` from the latest release.
2.  (Optional) Add the location of `kjudge.exe` to your system's **PATH** environment variable to run it from anywhere.

Verify the installation:
```bash
kjudge --version
```

## 2. Initialize your first problem

Create a folder for a problem (e.g., `Watermelon`) and move into it:

```bash
mkdir Watermelon
cd Watermelon
```

Now, initialize kJudge in this folder. We'll use C++ for this example:

```bash
kjudge init --lang cpp
```

This creates a hidden `.kjudge` folder for metadata and a starter `main.cpp`.

## 3. Add Sample Tests

You can add sample test cases manually. Let's add a simple one (e.g., 8 -> YES):

```bash
kjudge add
```
- **Input**: Paste `8` and press Enter, then Ctrl+Z (or Ctrl+D) to finish.
- **Output**: Paste `YES` and press Enter, then Ctrl+Z (or Ctrl+D) to finish.

## 4. Run and Solve

Now, write your solution in `main.cpp`. When ready, run kJudge to test it against your samples:

```bash
kjudge run main.cpp
```

kJudge will compile your code, run it against all samples in `.kjudge/tests/`, and show you a clean AC/WA/TLE report.

---

**Next Steps:**
- Learn how to [Fetch Codeforces Samples](../how-to/handle-contests.md) automatically.
- Explore the [CLI Reference](../reference/cli.md) for advanced flags.
