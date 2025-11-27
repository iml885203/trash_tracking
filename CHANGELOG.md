# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Calendar Versioning](https://calver.org/) (YYYY.MM.MICRO).

## [2025.11.12] - 2025-11-28

### Fixed
- **Critical**: Fixed state flapping issue where status repeatedly jumped between "idle" and "nearby"
- **Critical**: Fixed sensor stuck in "nearby" state until schedule ends
- **Critical**: Schedule-based polling now correctly detects collection days
- **Truck Info**: Fixed sensor flapping between showing location and "No truck nearby"
- Truck Info now always displays location when available, regardless of state

### Changed
- **Truck Info Sensor**: Now displays current location and progress (e.g., "民生路二段80號 (23/69)")
- **API Cache**: Reduced cache TTL from 60s to 5s to prevent stale data
- **Performance**: Reduced update interval from 90s to 30s for more responsive tracking
- **Simplified trigger logic**: Removed "arriving" mode - notifications now trigger when truck arrives at entry point
- **Config Flow**: Simplified UI - removed trigger mode and approaching threshold selectors

### Added
- **BDD Tests**: New `truck_tracking.feature` with 6 scenarios for state management

### Technical
- PointMatcher now state-aware and checks exit_point status before triggering
- StatusResponseBuilder returns truck info regardless of state
- Major core refactoring with TruckStateMachine, StatusResponseBuilder, TrackingWindow

## [2025.11.10] - 2025-11-23

### Fixed
- **Critical**: Fixed "No module named 'trash_tracking_core'" error when adding integration
- Synced core package to custom_components with API optimizations

## [2025.11.9] - 2025-11-23

### Changed
- **API Optimization**: Intelligent schedule-based polling to reduce unnecessary API calls
- **API Optimization**: Class-level caching in NTPC API client for improved performance
- **Performance**: Significantly reduced API request frequency during non-collection hours

### Added
- **Testing**: Comprehensive unit test suite (111 tests) for core modules
- **Testing**: Module-level tests for TruckTracker, Geocoding, and RouteAnalyzer
- **Documentation**: Two-layer testing strategy (BDD + Unit tests)

### Technical
- Test coverage improved with unit tests for API client caching behavior
- Restructured tests from feature-oriented to module-oriented organization
- Added complexity analysis documentation

## [2025.11.8] - 2025-11-23

### Added
- **GitHub Actions**: Hassfest validation workflow (required for HACS)
- **GitHub Actions**: HACS Action validation workflow
- **CI/CD**: Automated validation on push, PR, and scheduled runs

### Changed
- **HACS Compliance**: All validation workflows now passing
- **Documentation**: Updated release process in CLAUDE.md

## [2025.11.7] - 2025-11-23

### Added
- Initial release of Trash Tracking integration for Home Assistant
- Real-time garbage truck tracking for New Taipei City
- Config flow with address geocoding support
- Binary sensor for truck nearby status
- Info sensor with detailed truck information
- Support for custom entry/exit points
- Two trigger modes: "arriving" and "arrived"
- Automated sync script for core package maintenance
- Comprehensive test suite (pytest + behave BDD)
- MIT License

### Features
- **Address Geocoding**: Automatic conversion of Taiwan addresses to GPS coordinates
- **Multi-API Support**: NLSC, Nominatim, and TGOS geocoding services
- **Route Analysis**: Smart collection point recommendations
- **State Management**: Idle/Nearby state machine for automations
- **Home Assistant Integration**: Full UI config flow, no YAML needed

### Technical
- Monorepo structure with shared core package
- Code quality: Pylint 9.2/10, 100% flake8 compliant
- Test coverage: 42% (unit tests + BDD integration tests)
- Pre-commit hooks for code quality
- CI/CD with GitHub Actions

[2025.11.12]: https://github.com/iml885203/trash_tracking/releases/tag/v2025.11.12
[2025.11.10]: https://github.com/iml885203/trash_tracking/releases/tag/v2025.11.10
[2025.11.9]: https://github.com/iml885203/trash_tracking/releases/tag/v2025.11.9
[2025.11.8]: https://github.com/iml885203/trash_tracking/releases/tag/v2025.11.8
[2025.11.7]: https://github.com/iml885203/trash_tracking/releases/tag/v2025.11.7
