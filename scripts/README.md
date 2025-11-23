# Scripts

Utility scripts for maintaining the trash_tracking project.

## sync_core.py

Synchronizes the core package from `packages/core/` to `custom_components/trash_tracking/`.

**Usage:**
```bash
python3 scripts/sync_core.py
```

**What it does:**
1. Copies all files from `packages/core/trash_tracking_core/` to `custom_components/trash_tracking/trash_tracking_core/`
2. Converts absolute imports (`from trash_tracking_core.xxx`) to relative imports (`from .xxx`, `from ..xxx`)
3. Preserves directory structure and ensures code consistency

**When to use:**
- After making any changes to `packages/core/trash_tracking_core/`
- Before committing changes that affect the core logic
- To ensure both versions stay synchronized

**Important:** Never edit `custom_components/trash_tracking/trash_tracking_core/` directly. Always edit `packages/core/` and run this sync script.
