# Development Guide

## Overview

This guide covers development setup and best practices for the Trash Tracking Home Assistant integration.

---

## Setup Development Environment

### 1. Clone Repository

```bash
git clone https://github.com/iml885203/trash_tracking.git
cd trash_tracking
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install core package in editable mode
pip install -e packages/core/

# Install CLI package (optional)
pip install -e apps/cli/

# Install development dependencies
pip install -r requirements-dev.txt
```

### 4. Install Git Hooks

We use `pre-commit` to enforce code quality standards automatically.

```bash
# Install pre-commit hooks
pre-commit install
pre-commit install --hook-type pre-push
```

---

## Project Structure

```
trash_tracking/
├── packages/core/                     # Core business logic package
│   ├── trash_tracking_core/          # Source code
│   ├── setup.py                      # Package configuration
│   └── README.md                     # Core package docs
├── custom_components/                 # Home Assistant Integration
│   └── trash_tracking/
│       ├── trash_tracking_core/      # Embedded core (synced from packages/core)
│       ├── __init__.py               # Integration entry point
│       ├── config_flow.py            # Setup wizard
│       ├── coordinator.py            # Data coordinator
│       ├── sensor.py                 # Sensor platform
│       ├── binary_sensor.py          # Binary sensor platform
│       └── manifest.json             # Integration metadata
├── apps/cli/                          # CLI tool (optional)
├── tests/                             # Unit tests
├── docs/                              # Documentation
└── scripts/                           # Development scripts
```

---

## Code Quality Checks

### Pre-commit Hooks (Runs on `git commit`)

Automatically runs before each commit:

1. **Trailing whitespace removal**
2. **End-of-file fixer**
3. **YAML syntax check**
4. **Large files check**
5. **Black** - Code formatting
6. **isort** - Import sorting
7. **flake8** - Linting

### Manual Checks

#### Formatting

```bash
# Format code with black
black packages/core/trash_tracking_core custom_components/trash_tracking apps/cli

# Sort imports with isort
isort packages/core/trash_tracking_core custom_components/trash_tracking apps/cli
```

#### Linting

```bash
# Run flake8
flake8 packages/core/trash_tracking_core custom_components/trash_tracking apps/cli --count --max-line-length=120

# Run pylint
pylint packages/core/trash_tracking_core
```

#### Type Checking

```bash
# Run mypy
mypy packages/core/trash_tracking_core --ignore-missing-imports --no-strict-optional
```

---

## Testing

### Unit Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=packages/core/trash_tracking_core --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_tracker.py -v

# Run specific test
pytest tests/test_tracker.py::test_tracker_idle_state -v

# Run with debugging
pytest --pdb
```

### Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=packages/core/trash_tracking_core --cov-report=html

# View report (opens in browser)
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Test Structure

```
tests/
├── test_tracker.py           # Tracker tests
├── test_state_manager.py     # State manager tests
├── test_point_matcher.py     # Point matcher tests
├── test_geocoding.py         # Geocoding tests
└── conftest.py               # Shared fixtures
```

---

## Developing the Integration

### Testing in Home Assistant

1. **Copy integration to HA config**:
   ```bash
   # Create symlink to custom_components
   ln -s $(pwd)/custom_components/trash_tracking /path/to/homeassistant/config/custom_components/
   ```

2. **Restart Home Assistant**

3. **Add integration via UI**:
   - Settings → Devices & Services
   - Add Integration → Search "Trash Tracking"

### Debugging

Enable debug logging in Home Assistant's `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.trash_tracking: debug
    trash_tracking_core: debug
```

View logs:
```bash
# Follow Home Assistant logs
tail -f /path/to/homeassistant/home-assistant.log | grep trash_tracking
```

### Hot Reload

Changes to Python files require Home Assistant restart, but you can reload the integration without full restart:

1. Developer Tools → YAML → Reload "All YAML configuration"
2. Or restart Home Assistant

---

## Syncing Core Package

The core package (`packages/core/trash_tracking_core/`) is embedded in the integration at `custom_components/trash_tracking/trash_tracking_core/`.

**Sync script** (if exists):
```bash
./scripts/sync_core.sh
```

**Manual sync**:
```bash
rsync -av --delete packages/core/trash_tracking_core/ custom_components/trash_tracking/trash_tracking_core/
```

---

## CLI Tool Development

The CLI tool is useful for testing core functionality without Home Assistant:

```bash
# Run CLI directly
cd apps/cli
python cli.py --lat 25.018269 --lng 121.471703

# Or use as module
python -m trash_tracking_cli --suggest "新北市板橋區民生路二段80號"
```

---

## Git Workflow

### Branching Strategy

- `master` - Production-ready code
- `develop` - Development branch (if used)
- `feature/*` - Feature branches
- `fix/*` - Bug fix branches

### Commit Messages

Follow conventional commits:

```
feat: add support for multiple routes
fix: correct state transition logic
docs: update README installation steps
test: add tests for point matcher
chore: update dependencies
```

### Pre-commit Checks

Before committing, ensure:

1. All tests pass: `pytest`
2. Code is formatted: `black .` and `isort .`
3. No linting errors: `flake8 .`
4. Type checking passes: `mypy packages/core/trash_tracking_core`

Pre-commit hooks will automatically check most of these.

---

## Release Process

### Version Bumping

This project uses CalVer (Calendar Versioning): `YYYY.MM.PATCH`

Example: `2025.11.7`

**Update version in**:
1. `custom_components/trash_tracking/manifest.json`
2. `packages/core/setup.py`
3. `VERSION` file (if exists)

### Creating a Release

1. **Update version numbers**:
   ```bash
   # Update manifest.json
   vim custom_components/trash_tracking/manifest.json

   # Update setup.py
   vim packages/core/setup.py
   ```

2. **Commit changes**:
   ```bash
   git add -A
   git commit -m "chore: bump version to 2025.11.X"
   ```

3. **Create tag**:
   ```bash
   git tag -a v2025.11.X -m "Release 2025.11.X"
   git push origin master --tags
   ```

4. **CI/CD will**:
   - Run tests
   - Build integration
   - Create GitHub release

---

## CI/CD Pipeline

The project uses GitHub Actions for CI/CD (`.github/workflows/ci.yml`):

### Test Job

Runs on every push and PR:

1. **Setup**: Python 3.11 and 3.12
2. **Lint**: flake8 checks
3. **Format**: black and isort verification
4. **Type check**: mypy
5. **Tests**: pytest with coverage
6. **Upload**: Coverage reports to Codecov

### Triggers

- **Push** to `master` or `develop`
- **Pull requests** to `master` or `develop`
- **Tags** starting with `v*`

---

## Common Development Tasks

### Adding a New Sensor Attribute

1. Update `binary_sensor.py` or `sensor.py`
2. Modify `coordinator.py` if new data needed
3. Update tests
4. Update documentation

### Adding a New Config Option

1. Add constant to `const.py`
2. Update `config_flow.py` schema
3. Update `coordinator.py` to use new option
4. Add migration logic if needed (in `__init__.py`)
5. Update documentation

### Debugging API Issues

```python
# Enable requests logging
import logging
import http.client as http_client

http_client.HTTPConnection.debuglevel = 1
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True
```

---

## Troubleshooting

### Common Issues

**Issue**: Pre-commit hooks fail
```bash
# Solution: Run hooks manually and fix issues
pre-commit run --all-files
```

**Issue**: Import errors in tests
```bash
# Solution: Reinstall core package
pip install -e packages/core/
```

**Issue**: Integration not showing in HA
```bash
# Solution: Check manifest.json syntax
python -m json.tool custom_components/trash_tracking/manifest.json
```

**Issue**: Coordinator not updating
```bash
# Solution: Check HA logs for errors
# Enable debug logging in configuration.yaml
```

---

## Resources

- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [Home Assistant Architecture](https://developers.home-assistant.io/docs/architecture_index)
- [Config Flow Handler](https://developers.home-assistant.io/docs/config_entries_config_flow_handler)
- [DataUpdateCoordinator](https://developers.home-assistant.io/docs/integration_fetching_data)
- [Integration Quality Scale](https://developers.home-assistant.io/docs/integration_quality_scale_index)

---

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/iml885203/trash_tracking/issues)
- **Discussions**: [GitHub Discussions](https://github.com/iml885203/trash_tracking/discussions)
- **Home Assistant Community**: [Community Forum](https://community.home-assistant.io/)

---

**Happy coding! 🚀**
