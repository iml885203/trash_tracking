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
│   ├── addon/                      # Home Assistant Add-on (Flask API)
│   │   ├── addon/api/              # Flask routes
│   │   ├── addon/use_cases/        # Setup wizard logic
│   │   └── app.py                  # Entry point
│   └── cli/                        # CLI tool (cli.py)
├── features/                       # BDD tests (Behave)
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

# 3. Install addon and CLI packages
pip install -e apps/addon/
pip install -e apps/cli/  # if developing CLI

# 4. Install dev dependencies
pip install -r requirements-dev.txt

# 5. Install pre-commit hooks
pre-commit install
```

## Common Commands

### Running Tests

```bash
# Activate venv first
source .venv/bin/activate

# Run all unit tests (pytest)
pytest

# Run with coverage
pytest --cov=packages/core/trash_tracking_core --cov-report=html

# Run specific test
pytest tests/test_point_matcher.py -v

# Run BDD tests (Behave) with mock API
USE_MOCK_API=true python -m behave features/ -v

# Run BDD tests without mock (requires Flask server running)
python -m behave features/ -v
```

### Code Quality

```bash
# Linting (all source directories)
flake8 packages/core/trash_tracking_core apps/addon/addon apps/cli features --count --max-line-length=120

# Format code
black packages/core/trash_tracking_core apps/addon/addon apps/cli features
isort packages/core/trash_tracking_core apps/addon/addon apps/cli features

# Type checking
mypy packages/core/trash_tracking_core --ignore-missing-imports --no-strict-optional
```

### Running the Application

```bash
# Run Flask API server (addon)
cd apps/addon/
cp config.example.yaml config.yaml  # First time only
python app.py

# Run CLI tool
cd apps/cli/
python cli.py --lat 25.018269 --lng 121.471703
python cli.py --suggest "新北市板橋區民生路二段80號"
```

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

### Mock API for Testing
BDD tests use a mock API system controlled by `USE_MOCK_API` environment variable:
- `USE_MOCK_API=true`: Uses mock data from `features/fixtures/mock_api_data.py`
- `USE_MOCK_API=false`: Uses real NTPC API (requires Flask server running)

**Critical**: When mocking methods in tests, ensure the method names match exactly. For example:
- `Geocoder.address_to_coordinates` (NOT `geocode`)
- `NTPCApiClient.get_around_points` (NOT `get_trucks`)

See `features/environment.py:75-80` for the correct mock setup.

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

- **Unit tests** (`tests/`): Test individual modules with pytest, mock external APIs
- **BDD tests** (`features/`): End-to-end scenarios with Behave (Gherkin syntax)
  - API status queries
  - CLI commands
  - Setup wizard workflow

BDD tests use mock API by default in CI to avoid external dependencies.

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`):
1. **Test job**: Runs on Python 3.11 and 3.12
   - Linting (flake8)
   - Code formatting check (black, isort)
   - Type checking (mypy)
   - Starts Flask server in background
   - Runs BDD tests with mock API
2. **Build images**: Multi-architecture Docker builds (amd64, aarch64, armv7)
3. **Update addon repo**: Triggers repository dispatch to homeassistant-addons repo

**Important for CI debugging**: BDD tests fail if mocks are incorrectly configured. Always verify method names match the actual implementation.

## Configuration

Configuration is in YAML format (`apps/addon/config.yaml`):

```yaml
location:
  lat: 25.018269
  lng: 121.471703

tracking:
  target_lines: ["C08 Afternoon Route"]
  enter_point: "Minsheng Rd. Sec. 2, No. 80"
  exit_point: "Chenggong Rd. No. 23"
  trigger_mode: "arriving"      # "arriving" or "arrived"
  approaching_threshold: 2       # Stops ahead for notification
```

## Home Assistant Integration

The addon provides a REST API that Home Assistant polls:
- `GET /health`: Health check
- `GET /api/trash/status`: Returns `{status: "idle"|"nearby", reason: "...", truck: {...}}`
- `POST /api/reset`: Reset tracker state (testing only)

Users configure RESTful sensors in HA to consume this API. See README.md for integration examples.

## Important Files

- `packages/core/trash_tracking_core/core/tracker.py`: Main tracking logic
- `packages/core/trash_tracking_core/core/point_matcher.py`: Collection point matching (entry/exit detection)
- `packages/core/trash_tracking_core/core/state_manager.py`: State machine
- `packages/core/trash_tracking_core/clients/ntpc_api.py`: NTPC API client
- `apps/addon/addon/api/routes.py`: Flask API endpoints
- `features/environment.py`: BDD test setup (mocks configuration)

## Git Configuration

**Critical for cross-platform development**: This project enforces LF line endings via `.gitattributes` to ensure consistency across Windows/Linux/macOS. Git is configured to normalize line endings on commit.

If you encounter line ending issues, run:
```bash
git add --renormalize .
```

See `docs/GIT_CONFIGURATION.md` for details.
