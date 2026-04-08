# kjudge v1.0.0

I'm incredibly excited to announce the first stable release of **kjudge**! I built this CLI tool from the ground up to completely automate the frustrating parts of competitive programming: managing test cases, compiling code, finding bugs, and executing stress tests locally. 

This release marks the transition from standard execution pipelines to an incredibly robust, automated sandboxing architecture capable of fetching samples securely and executing solutions transparently.

## Key Features in v1.0.0

- **Anti-Bot Fetching Engine:** I've integrated `cloudscraper` directly into the web-scraping core. You can now use `kjudge fetch cf:4A` or `kjudge contest cf:2050` and cleanly pull Codeforces test cases dynamically without ever hitting Cloudflare's `403 Forbidden` JS challenges.
- **Smart Stress Testing:** Brute-force random inputs against your optimized solution using `kjudge stress --brute brute.cpp --smart main.cpp --gen "python gen.py"`. It will halt instantly and display the exact discrepancy in colored diff when it finds a mismatch.
- **Contest Scaffolding & Watch Mode:** Run `kjudge contest cf:1234` to automatically initialize the entire contest environment, or use `kjudge watch main.cpp` to instantly rerun tests the millisecond you hit "Save" on your editor.
- **Custom Native Checkers:** Fully supports custom checker scripts, token matching, and float epsilon matching (e.g. `--checker float:1e-6`).

## Zero-Friction Setup Wizard

If you download the standalone `kjudge.exe` below, you don't even need Python or PIP. 
Just double-click the `.exe` file! I specifically wrote an **Interactive Setup Wizard** that will spawn instantly. It safely copies the binary to `~/.kjudge/bin` and permanently pushes it into your Windows Global `PATH`. 

Once you restart your terminal, you can literally type `kjudge` in any folder on your computer!

## Assets & Downloads
- **kjudge.exe** - The globally accessible Setup Wizard & Executable.
- **Source Code (zip / tar.gz)**

Have fun, and happy coding!
— Byte-ne
