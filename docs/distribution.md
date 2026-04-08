

# Package Distribution & Standalone Builds

Extensive details on how to deploy and retrieve `kjudge` instances bypassing traditional version control structures.

## 1. Python PyPI Distribution Model

A user does not need to execute `git clone`. Because the module is built natively against `setuptools` with a `pyproject.toml` definition, it can be fetched explicitly across external HTTPS nodes using pip executable.

```bash
pip install git+https://github.com/Byte-ne/kJudge.git
```
This runs the internal `setuptools` build-chain, installs it securely into the OS `site-packages` directory, and registers the `kjudge` binary to the system PATH.

## 2. Fully Standalone PE Compilation (PyInstaller)

In competitive programming scenarios involving restricted terminals (Live coding rounds, isolated VM sandboxes without PIP), a user commands the pre-compiled `.exe`.

the repository maintains `kjudge.exe`, a deployment bootstrapper.
- It validates the `PyInstaller` toolkit.
- Ingests the `__main__.py` bridging script.
- Packages all requisite `rich`, `bs4`, and `requests` wheels inside the executable sandbox wrapper.

advised to download via **Github Releases**, which would allow programmers to run kJudge on their machine without PIP or Python.