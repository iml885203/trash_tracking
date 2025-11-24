# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Calendar Versioning](https://calver.org/) (YYYY.MM.MICRO).

## [2025.11.12b1] - 2025-11-24

### BREAKING CHANGES
- **Simplified trigger logic**: Removed "arriving" mode and "approaching_threshold" setting
- All notifications now trigger when truck **actually arrives** at entry point (not N stops ahead)
- If you previously used "arriving" mode, you may experience **later notifications** after this update
- Config flow no longer shows trigger mode selection

### Changed
- **RouteAnalyzer**: Now recommends `enter_point = nearest_point - 1` for better timing
- **Status Sensor**: Added configuration attributes (enter_point, exit_point, schedule info)
- **Config Flow**: Simplified UI - removed trigger mode and approaching threshold selectors

### Technical
- Removed trigger_mode and approaching_threshold from all core modules
- PointMatcher simplified to use only "arrived" logic
- Old configurations remain functional (ignored parameters won't cause errors)

### Notes
This is a beta release for testing the simplified trigger logic.
Existing users should re-add the integration if they want to use the new recommendation logic.

## [2025.11.11b2] - 2025-11-24

### Changed
- **Performance**: Reduced update interval from 90s to 30s for more responsive tracking
- **Logging**: Added route name prefix to all schedule-related debug logs

### Technical
- Update interval now 30s (from 90s) - safe with schedule-based polling
- Debug logs now show `[route_name]` prefix for easier troubleshooting
- Estimated API calls: ~1,170/week (still 77% reduction from original 5,040/week)

## [2025.11.11b1] - 2025-11-24

### Fixed
- **Critical**: Schedule-based polling now correctly detects collection days
- Fixed PointWeekKnd interpretation (waste types, not weekdays)
- Config flow now queries API 7 times to determine actual collection days

### Changed
- _extract_schedule_from_route() now actively determines collection days via API
- Config flow shows correct weekdays in debug log after this fix

### Known Issues
- **Beta**: Requires re-adding integration to apply schedule detection
- Existing integrations will continue to poll API every 2 minutes until re-added

### Notes
This is a beta release for testing the schedule detection fix.
Please test and report any issues before stable release.

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

[2025.11.12b1]: https://github.com/iml885203/trash_tracking/releases/tag/v2025.11.12b1
[2025.11.11b2]: https://github.com/iml885203/trash_tracking/releases/tag/v2025.11.11b2
[2025.11.11b1]: https://github.com/iml885203/trash_tracking/releases/tag/v2025.11.11b1
[2025.11.10]: https://github.com/iml885203/trash_tracking/releases/tag/v2025.11.10
[2025.11.9]: https://github.com/iml885203/trash_tracking/releases/tag/v2025.11.9
[2025.11.8]: https://github.com/iml885203/trash_tracking/releases/tag/v2025.11.8
[2025.11.7]: https://github.com/iml885203/trash_tracking/releases/tag/v2025.11.7
