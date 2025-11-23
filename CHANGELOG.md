# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Calendar Versioning](https://calver.org/) (YYYY.MM.MICRO).

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

[2025.11.7]: https://github.com/iml885203/trash_tracking/releases/tag/v2025.11.7
