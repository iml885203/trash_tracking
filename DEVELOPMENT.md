# Development Guide

Quick reference for developers working on the Trash Tracking integration.

> **Note**: For detailed documentation including release process, testing, and sync scripts, see [CLAUDE.md](CLAUDE.md).

---

## Quick Start

### 1. Setup Environment

```bash
# Clone and setup
git clone https://github.com/iml885203/trash_tracking.git
cd trash_tracking

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e packages/core/
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 2. Project Structure

```
trash_tracking/
├── packages/core/                     # Core business logic (source of truth)
│   └── trash_tracking_core/          # Shared Python package
├── custom_components/                 # Home Assistant Integration
│   └── trash_tracking/
│       ├── trash_tracking_core/      # Embedded core (synced via script)
│       ├── config_flow.py            # Setup wizard
│       ├── coordinator.py            # Data coordinator
│       └── sensor.py                 # Sensor platforms
├── tests/                             # Unit tests (pytest)
├── features/                          # BDD tests (behave)
└── scripts/                           # Development scripts
```

**Important**: Always edit `packages/core/`, then sync to `custom_components/` using:
```bash
python3 scripts/sync_core.py
```

---

## Common Tasks

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=packages/core/trash_tracking_core --cov-report=html

# Run BDD tests
python -m behave features/
```

### Code Quality

```bash
# Linting (all checks)
flake8 packages/core/trash_tracking_core custom_components/trash_tracking --count --max-line-length=120

# Format code
black packages/core/trash_tracking_core custom_components/trash_tracking
isort packages/core/trash_tracking_core custom_components/trash_tracking

# Type checking
mypy packages/core/trash_tracking_core --ignore-missing-imports --no-strict-optional
```

**Pre-commit hooks** automatically run black, isort, and flake8 on commit.

### Testing in Home Assistant

1. **Symlink to HA config**:
   ```bash
   ln -s $(pwd)/custom_components/trash_tracking /path/to/homeassistant/config/custom_components/
   ```

2. **Enable debug logging** in `configuration.yaml`:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.trash_tracking: debug
       trash_tracking_core: debug
   ```

3. **Restart Home Assistant** and add integration via UI

---

## Development Workflow

### Making Changes

1. Edit code in `packages/core/trash_tracking_core/`
2. Run tests: `pytest`
3. Sync to integration: `python3 scripts/sync_core.py`
4. Test in Home Assistant
5. Commit with conventional commits:
   ```
   feat: add new feature
   fix: fix bug
   docs: update docs
   test: add tests
   chore: maintenance
   ```

### Releasing

See [CLAUDE.md - Creating a New Release](CLAUDE.md#creating-a-new-release) for the complete release process.

**Quick summary**:
1. Update version in `manifest.json` and `pyproject.toml`
2. Update `CHANGELOG.md`
3. Commit and push
4. Create and push git tag: `git tag vYYYY.MM.MICRO && git push origin vYYYY.MM.MICRO`
5. GitHub Actions automatically creates release

---

## Debugging

### Common Issues

**Pre-commit hooks fail**:
```bash
pre-commit run --all-files  # Run manually to see errors
```

**Import errors in tests**:
```bash
pip install -e packages/core/  # Reinstall in editable mode
```

**Integration not showing in HA**:
```bash
python -m json.tool custom_components/trash_tracking/manifest.json  # Check syntax
```

### Logs

```bash
# Follow HA logs
tail -f /path/to/homeassistant/home-assistant.log | grep trash_tracking
```

---

## Resources

- **CLAUDE.md** - Complete development documentation
- **README.md** - User installation guide
- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [GitHub Issues](https://github.com/iml885203/trash_tracking/issues)

---

**For comprehensive documentation, see [CLAUDE.md](CLAUDE.md)**
