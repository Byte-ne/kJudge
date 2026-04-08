

# Config Parsing and System Mechanics

How kjudge resolves complex user preferences overriding local settings safely.

## 1. JSON Merge Hierarchy

Configuration is hydrated dynamically based on a rigid priority matrix.
Priority Level (Highest to Lowest):
1. **Positional Arguments / CLI Flags** (e.g., `--time 5000`)
2. **Local Repository Environment** (`.kjudge/config.json`)
3. **Global Terminal State** (`~/.kjudge/config.json`)

The resolution engine implements a shallow dictionary overlay logic:
```python
# In config.py logic equivalent:
merged = global_cfg.copy()
merged.update(local_cfg)
merged = override_with_pydantic_like_cli(merged, cli_args)
```

## 2. Dynamic Language Injection

`kjudge` acts as a polyglot dispatcher. Upon initialization, it dynamically allocates build compilation strings derived conditionally via OS architecture checks (e.g., executing `os.name == 'nt'` resolves to `.exe` PE binaries on Windows, and strict ELF execution strings `./main` on POSIX systems).

Template initialization strings are loaded natively as statically bundled multi-line attributes but gracefully yield if user-injected templating exists under `~/.kjudge/templates/main.cpp`. This file overwrite sequence circumvents permission complexities.

## 3. Target Sanitizing and Artifact Archiving

When using `kjudge clean --build`, `kjudge` iterates over binary target signatures dynamically. It wipes explicit bytecode caching via `__pycache__` destruction trees, Java compiled `.class` nodes, and explicit binary names mapped natively via the JSON routing config. This garbage collection ensures clean deployment runs for isolated regression testing.
