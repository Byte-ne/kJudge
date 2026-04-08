# Package Distribution & Standalone Builds

Extensive details on how to deploy and retrieve `kjudge` instances bypassing traditional version control structures.

## 1. Python PyPI Distribution Model (Preferred approach)

A user does not need to execute `git clone`. Because the module is built natively against `setuptools` with a `pyproject.toml` definition, it can be fetched explicitly across external HTTPS nodes using pip executable.

```bash
pip install git+https://github.com/Username/kJudge.git
```
This runs the internal `setuptools` build-chain, installs it securely into the OS `site-packages` directory, and registers the `kjudge` binary to the system PATH.

## 2. Fully Standalone PE Compilation (PyInstaller)

In competitive programming scenarios involving restricted terminals (Live coding rounds, isolated VM sandboxes without PIP), a user commands the pre-compiled `.exe`.

On the host machine, the repository maintains `build_executable.py`, a deployment bootstrapper.
- It validates the `PyInstaller` toolkit.
- Ingests the `__main__.py` bridging script.
- Generates a static, dynamically linked binary payload (using the `--onefile` payload compression flag).
- Packages all requisite `rich`, `bs4`, and `requests` wheels inside the executable sandbox wrapper.

Host maintainers are advised to distribute via **GitHub Releases**. Allowing competitors to run a single `wget` or direct-download onto their filesystem without ever exposing Python configurations.

## 3. Zip Artifact Exportation

The `kjudge export payload.zip` functionality allows atomic state transfers. It serializes the entire testing topology (all nested `.kjudge/tests` nodes + local execution configs) via LZMA or Deflated compression arrays yielding <100kb payloads for immediate peer-to-peer distribution.
