# Changelog

All notable changes to this add-on will be documented in this file.

## [1.0.0] - 2025-11-18

### Added
- Initial release of Trash Tracking Add-on
- Real-time New Taipei City garbage truck tracking
- Support for multiple route tracking
- Custom entry/exit point configuration
- Two trigger modes: `arriving` (with threshold) and `arrived`
- RESTful API for Home Assistant integration
- Multi-architecture support (aarch64, amd64, armhf, armv7, i386)
- Health check endpoint
- Comprehensive documentation (README, DOCS)
- CLI tool for finding cleanup point names
- Auto-configuration via Home Assistant UI
- Debug logging support

### Features
- ✅ Real-time garbage truck position tracking
- ✅ Customizable entry/exit cleanup points
- ✅ Multi-route tracking support
- ✅ RESTful API integration
- ✅ Automatic Home Assistant integration
- ✅ UI-based configuration (no YAML editing required)
- ✅ Multi-language support (Chinese/English)

### Configuration
- Location settings (latitude/longitude)
- Tracking settings (target routes, entry/exit points, trigger mode)
- System settings (log level)
- API settings (timeout, retry configuration)

### API Endpoints
- `GET /api/trash/status` - Get current garbage truck status
- `GET /health` - Health check
- `POST /api/reset` - Reset tracker state (testing)

### Documentation
- Installation guide
- Configuration examples
- Troubleshooting guide
- Home Assistant automation examples
- API reference
