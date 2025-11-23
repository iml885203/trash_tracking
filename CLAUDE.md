# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Real-time garbage truck tracking system for New Taipei City, Taiwan. Tracks trucks using the NTPC Environmental Protection Bureau API and integrates with Home Assistant for automation (e.g., turn on lights when truck approaches).

**Key workflow**: Truck approaching entry point → API status: nearby → HA automation → 💡 Light ON

## Monorepo Structure

This project uses a monorepo architecture with shared core logic:

```
trash_tracking/
├── packages/core/                  # Shared core package (trash-tracking-core)
│   └── trash_tracking_core/
│       ├── clients/                # API clients (NTPCApiClient)
│       ├── models/                 # Data models (Point, TruckLine)
│       ├── core/                   # Business logic (Tracker, StateManager, PointMatcher)
│       └── utils/                  # Utilities (Config, Geocoding, Logger)
├── apps/
│   └── cli/                        # CLI tool
├── custom_components/              # Home Assistant Integration
│   └── trash_tracking/             # Integration implementation
│       ├── trash_tracking_core/    # Embedded core package
│       ├── config_flow.py          # Setup wizard
│       ├── coordinator.py          # Data coordinator
│       └── sensor.py               # Sensor entities
└── tests/                          # Unit tests (pytest)
```

**Important**: All apps depend on the `trash-tracking-core` package. Install it in editable mode when developing:
```bash
pip install -e packages/core/
```

## Development Setup

```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. Install core package in editable mode
pip install -e packages/core/

# 3. Install CLI package (optional)
pip install -e apps/cli/

# 4. Install dev dependencies
pip install -r requirements-dev.txt

# 5. Install pre-commit hooks
pre-commit install
```

## Syncing Core Package

**IMPORTANT**: The `trash_tracking_core` package exists in two locations:
- `packages/core/trash_tracking_core/` - Source of truth (with absolute imports)
- `custom_components/trash_tracking/trash_tracking_core/` - Embedded copy for Home Assistant (with relative imports)

After making changes to the core package, **always run the sync script**:

```bash
python3 scripts/sync_core.py
```

This script:
1. Copies all files from packages/core/ to custom_components/
2. Converts absolute imports to relative imports automatically
3. Ensures both versions stay in sync

**Never edit `custom_components/trash_tracking/trash_tracking_core/` directly!** Always edit `packages/core/` and sync.

## Common Commands

### Running Tests

This project uses a **two-layer testing strategy**:

1. **BDD Integration Tests** (Behave) - User-focused scenarios protecting main workflows
2. **Unit Tests** (pytest) - Module-level tests ensuring component functionality

```bash
# Activate venv first
source .venv/bin/activate

# Run BDD integration tests (user scenarios)
behave                              # All BDD scenarios
behave features/config_flow.feature # Specific feature

# Run unit tests (module tests)
pytest                              # All unit tests
pytest tests/models/                # Model tests only
pytest tests/core/test_state_manager.py -v  # Specific module

# Run with coverage
pytest --cov=packages/core/trash_tracking_core --cov-report=html

# Run all tests (BDD + Unit)
behave && pytest
```

**Test Organization:**
- `features/` - BDD scenarios (integration tests from user perspective)
- `tests/models/` - Point and TruckLine model tests
- `tests/clients/` - NTPC API client tests (including caching)
- `tests/core/` - PointMatcher, StateManager, Tracker tests

### Code Quality

```bash
# Linting (all source directories)
flake8 packages/core/trash_tracking_core apps/cli custom_components/trash_tracking --count --max-line-length=120

# Format code
black packages/core/trash_tracking_core apps/cli custom_components/trash_tracking
isort packages/core/trash_tracking_core apps/cli custom_components/trash_tracking

# Type checking
mypy packages/core/trash_tracking_core --ignore-missing-imports --no-strict-optional
```

### Running the Application

```bash
# Run CLI tool
cd apps/cli/
python cli.py --lat 25.018269 --lng 121.471703
python cli.py --suggest "新北市板橋區民生路二段80號"
```

### Creating a New Release

This project uses Calendar Versioning (CalVer: YYYY.MM.MICRO) and automated releases via GitHub Actions.

**Steps to release a new version:**

1. **Update version numbers**:
   - `custom_components/trash_tracking/manifest.json` - update `version` field
   - `pyproject.toml` - update `version` field

2. **Update CHANGELOG.md**:
   - Add new section for the version
   - Document all changes under appropriate categories (Added, Changed, Fixed, etc.)
   - Follow [Keep a Changelog](https://keepachangelog.com/) format

3. **Commit changes**:
   ```bash
   git add custom_components/trash_tracking/manifest.json pyproject.toml CHANGELOG.md
   git commit -m "chore: bump version to YYYY.MM.MICRO"
   git push origin master
   ```

4. **Create and push tag**:
   ```bash
   git tag vYYYY.MM.MICRO
   git push origin vYYYY.MM.MICRO
   ```

5. **Automated workflow** (`.github/workflows/release.yml`):
   - Automatically creates GitHub Release
   - Packages integration as `trash_tracking.zip`
   - Uploads ZIP to release assets
   - Extracts changelog content for release notes

**Version numbering examples:**
- `2025.11.7` - 7th release in November 2025
- `2025.12.1` - 1st release in December 2025
- `2026.1.10` - 10th release in January 2026

**After release:**
- Users on HACS will be notified of updates
- Manual installers can download ZIP from GitHub Releases

## Architecture & Design Patterns

### State Machine
The system uses a state machine to track truck status:
- **idle**: No trucks nearby (light off)
- **nearby**: Truck approaching/at collection point (light on)

State transitions are managed by `StateManager` in `packages/core/trash_tracking_core/core/state_manager.py`.

### Trigger Modes
- **arriving**: Trigger notification N stops before entry point (configurable via `approaching_threshold`)
- **arrived**: Trigger only when truck actually arrives at entry point

This logic is in `PointMatcher` (`packages/core/trash_tracking_core/core/point_matcher.py`).


## Key Concepts

### Collection Points
Each garbage truck route has multiple collection points with:
- **name**: e.g., "Minsheng Rd. Sec. 2, No. 80"
- **rank**: Order in the route (e.g., stop #12 out of 69)
- **time**: Scheduled arrival time

Users configure:
- **enter_point**: Light turns on when truck approaches
- **exit_point**: Light turns off when truck passes

### Geocoding
Address → GPS coordinates conversion for Taiwan addresses:
1. Tries NLSC API (National Land Surveying and Mapping Center)
2. Falls back to Nominatim (OpenStreetMap)
3. Falls back to TGOS (Taiwan Geographic Online Service)
4. Uses TWD97 → WGS84 coordinate conversion

Implementation: `packages/core/trash_tracking_core/utils/geocoding.py`

## Testing Strategy

This project uses a **two-layer testing approach** to ensure both user experience and code quality:

### Layer 1: BDD Integration Tests (User Perspective)
**Tool**: Behave (Gherkin syntax)
**Location**: `features/`
**Purpose**: Protect main user workflows from regressions

BDD tests are written from the user's perspective and cover critical end-to-end scenarios:
- **Config Flow**: Setting up garbage truck notifications (address input, route selection, point configuration)
- **CLI Queries**: Searching for nearby trucks, handling invalid addresses

**Example scenario** (`features/config_flow.feature`):
```gherkin
Scenario: 第一次設定我家的垃圾車通知
  假設 我住在 "新北市板橋區民生路二段80號"
  當 我在設定頁面輸入我家地址
  那麼 系統應該找到我家的位置座標
  而且 應該至少找到 1 條路線
```

**Benefits**:
- Tests actual user workflows
- Catches integration issues
- Serves as living documentation
- Easy for non-technical stakeholders to understand

### Layer 2: Unit Tests (Module Perspective)
**Tool**: pytest
**Location**: `tests/`
**Purpose**: Ensure individual components work correctly

Unit tests are organized by module and test isolated functionality:

```
tests/
├── models/          # Data model tests (Point, TruckLine)
├── clients/         # API client tests (NTPCApiClient, caching)
└── core/            # Business logic tests (PointMatcher, StateManager)
```

**Test coverage** (111 unit tests total):
- `tests/models/test_point.py` (30 tests): Point creation, status, weekday parsing, estimated arrival
- `tests/models/test_truck.py` (18 tests): TruckLine creation, point finding, upcoming points
- `tests/clients/test_ntpc_api.py` (18 tests): API calls, error handling, cache behavior
- `tests/core/test_point_matcher.py` (18 tests): Point matching logic, trigger modes
- `tests/core/test_state_manager.py` (27 tests): State transitions, timezone handling

**Benefits**:
- Fast execution (no external dependencies)
- Pinpoint exact failure locations
- Enable confident refactoring
- High code coverage (>80%)

### Testing Philosophy

**BDD tests** answer: "Does the system work for users?"
**Unit tests** answer: "Does each component work correctly?"

This two-layer approach provides:
1. **Confidence in releases**: BDD tests ensure user workflows don't break
2. **Maintainability**: Unit tests make refactoring safe
3. **Fast feedback**: Unit tests run quickly during development
4. **Documentation**: BDD scenarios document expected behavior

### Running Tests

```bash
# Run all tests (recommended before commit)
behave && pytest

# BDD only (integration tests)
behave

# Unit tests only
pytest

# With coverage
pytest --cov=packages/core/trash_tracking_core --cov-report=html
```

Coverage reports are uploaded to Codecov in CI.

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`):
1. **Test job**: Runs on Python 3.11 and 3.12
   - Linting (flake8)
   - Code formatting check (black, isort)
   - Type checking (mypy)
   - Unit tests with coverage

## Home Assistant Integration

The integration provides:
- **Config flow**: Setup wizard for easy configuration
- **Sensors**: Binary sensor (nearby/idle) and info sensor (truck details)
- **Coordinator**: Manages data updates and state tracking

Configuration is done through the Home Assistant UI. See README.md for installation and usage examples.

## Important Files

- `packages/core/trash_tracking_core/core/tracker.py`: Main tracking logic
- `packages/core/trash_tracking_core/core/point_matcher.py`: Collection point matching (entry/exit detection)
- `packages/core/trash_tracking_core/core/state_manager.py`: State machine
- `packages/core/trash_tracking_core/clients/ntpc_api.py`: NTPC API client
- `custom_components/trash_tracking/config_flow.py`: Integration setup wizard
- `custom_components/trash_tracking/coordinator.py`: Data coordinator
- `custom_components/trash_tracking/sensor.py`: Sensor entities

## Git Configuration

**Critical for cross-platform development**: This project enforces LF line endings via `.gitattributes` to ensure consistency across Windows/Linux/macOS. Git is configured to normalize line endings on commit.

If you encounter line ending issues, run:
```bash
git add --renormalize .
```

See `docs/GIT_CONFIGURATION.md` for details.
