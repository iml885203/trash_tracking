# 🚛 Trash Tracking - Home Assistant Integration

[![GitHub release](https://img.shields.io/github/v/release/iml885203/trash_tracking)](https://github.com/iml885203/trash_tracking/releases)
[![License](https://img.shields.io/github/license/iml885203/trash_tracking)](https://github.com/iml885203/trash_tracking/blob/master/LICENSE)
[![CI](https://github.com/iml885203/trash_tracking/actions/workflows/ci.yml/badge.svg)](https://github.com/iml885203/trash_tracking/actions)
[![HACS](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

Real-time garbage truck tracking integration for New Taipei City, Taiwan. Automatically trigger Home Assistant automations when trucks approach or pass your collection points.

## 📋 Overview

Track garbage trucks in real-time using the New Taipei City Environmental Protection Bureau API. Get notifications and trigger automations when trucks are near your location.

### ✨ Key Features

- 🚛 **Real-time Tracking**: Monitor New Taipei City garbage truck locations
- 📍 **Smart Collection Points**: Automatic route analysis and collection point suggestions
- 🎯 **Multi-route Support**: Track multiple garbage truck routes simultaneously
- ⏰ **Early Notification**: Configurable advance notification (N stops ahead)
- 🏠 **Native Integration**: Full Home Assistant integration with config flow
- 🔄 **Automatic Updates**: Real-time status updates via coordinator
- 🎨 **Binary Sensor**: Easy automation with nearby/idle states

### 🎬 Workflow

```
Truck approaching entry point → Binary Sensor: ON → HA automation → 💡 Light ON
Truck passing exit point → Binary Sensor: OFF → HA automation → 🌑 Light OFF
```

---

## 🚀 Installation

### Method 1: HACS (Recommended)

1. **Install Integration**
   - Open **HACS** in Home Assistant
   - Click on **Integrations**
   - Click **+ Explore & Download Repositories** (bottom right)
   - Search for "**Trash Tracking**"
   - Click **Download**
   - Restart Home Assistant

2. **Add Integration**
   - Go to Settings → Devices & Services
   - Click "+ Add Integration"
   - Search for "Trash Tracking"
   - Follow the setup wizard

### Method 2: HACS Custom Repository

If you cannot find the integration in the default HACS list yet:

1. **Add Custom Repository**
   - Open **HACS** in Home Assistant
   - Click on **Integrations**
   - Click the 3-dot menu (top right) → **Custom repositories**
   - Add repository URL: `https://github.com/iml885203/trash_tracking`
   - Category: **Integration**
   - Click **Add**

2. **Install Integration**
   - Search for "**Trash Tracking**" in HACS
   - Click **Download**
   - Restart Home Assistant

### Method 3: Manual Installation

1. **Download Integration**

   ```bash
   cd /config
   mkdir -p custom_components
   cd custom_components
   git clone https://github.com/iml885203/trash_tracking.git
   ```

2. **Copy Files**

   ```bash
   cp -r trash_tracking/custom_components/trash_tracking ./
   ```

3. **Restart Home Assistant**

4. **Add Integration**
   - Go to Settings → Devices & Services
   - Click "+ Add Integration"
   - Search for "Trash Tracking"
   - Follow the setup wizard

---

## ⚙️ Configuration

### Setup Wizard

The integration provides an easy-to-use setup wizard:

1. **Enter Your Address**
   - Input your address in Taiwan format
   - Example: `新北市板橋區民生路二段80號`

2. **Select Route**
   - The wizard will automatically find nearby garbage truck routes
   - Routes are sorted by distance from your location
   - Select the route that serves your area

3. **Configure Collection Points**
   - **Entry Point**: Truck status changes to "nearby" when arriving at this point
   - **Exit Point**: Truck status returns to "idle" when passing this point
   - Points are automatically suggested based on your location (entry point = nearest point - 1)

### Example Configuration

After setup, the integration creates:

**Binary Sensor**:

- `binary_sensor.trash_tracking_[route_name]_nearby`: ON when truck is near

**Sensor**:

- `sensor.trash_tracking_[route_name]_info`: Detailed truck information

---

## 🤖 Automation Examples

### Basic Light Automation

```yaml
automation:
  - alias: "Garbage Truck Approaching - Turn On Light"
    trigger:
      - platform: state
        entity_id: binary_sensor.trash_tracking_c08_afternoon_nearby
        to: "on"
    action:
      - service: light.turn_on
        target:
          entity_id: light.notification_bulb
        data:
          brightness: 255
          rgb_color: [255, 0, 0]

  - alias: "Garbage Truck Left - Turn Off Light"
    trigger:
      - platform: state
        entity_id: binary_sensor.trash_tracking_c08_afternoon_nearby
        to: "off"
    action:
      - service: light.turn_off
        target:
          entity_id: light.notification_bulb
```

### Mobile Notification

```yaml
automation:
  - alias: "Garbage Truck Notification"
    trigger:
      - platform: state
        entity_id: binary_sensor.trash_tracking_c08_afternoon_nearby
        to: "on"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "🚛 垃圾車來了！"
          message: "垃圾車正在接近，請準備倒垃圾"
          data:
            priority: high
            ttl: 0
```

### Play Audio Announcement

```yaml
automation:
  - alias: "Garbage Truck Audio Announcement"
    trigger:
      - platform: state
        entity_id: binary_sensor.trash_tracking_c08_afternoon_nearby
        to: "on"
    action:
      - service: tts.google_translate_say
        target:
          entity_id: media_player.living_room_speaker
        data:
          message: "垃圾車即將到達，請準備倒垃圾"
```

### Conditional Actions (Only on Weekdays)

```yaml
automation:
  - alias: "Garbage Truck Weekday Notification"
    trigger:
      - platform: state
        entity_id: binary_sensor.trash_tracking_c08_afternoon_nearby
        to: "on"
    condition:
      - condition: time
        weekday:
          - mon
          - tue
          - wed
          - thu
          - fri
    action:
      - service: light.turn_on
        target:
          entity_id: light.notification_bulb
```

---

## 📊 Sensor Attributes

### Binary Sensor Attributes

The binary sensor provides rich attributes for advanced automations:

```yaml
binary_sensor.trash_tracking_c08_afternoon_nearby:
  state: "on" # or 'off'
  attributes:
    current_point: "Minsheng Rd. Sec. 2, No. 80"
    current_rank: 12
    total_points: 69
    distance_meters: 45.2
    car_no: "ABC-1234"
    line_name: "C08 Afternoon Route"
    last_update: "2025-11-23T14:30:00"
```

### Using Attributes in Automations

```yaml
automation:
  - alias: "Announce Current Stop"
    trigger:
      - platform: state
        entity_id: binary_sensor.trash_tracking_c08_afternoon_nearby
        to: "on"
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: >
            垃圾車目前在：{{ state_attr('binary_sensor.trash_tracking_c08_afternoon_nearby', 'current_point') }}
            距離您：{{ state_attr('binary_sensor.trash_tracking_c08_afternoon_nearby', 'distance_meters') }} 公尺
```

---

## 🔧 CLI Tool (Optional)

For developers or advanced users, a CLI tool is available for testing:

```bash
# Install CLI tool
pip install -e apps/cli/

# Query trucks by coordinates
python -m trash_tracking_cli --lat 25.018269 --lng 121.471703

# Suggest configuration by address
python -m trash_tracking_cli --suggest "新北市板橋區民生路二段80號"

# Filter specific route
python -m trash_tracking_cli --lat 25.018269 --lng 121.471703 --line "C08"
```

---

## 🛠️ Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/iml885203/trash_tracking.git
cd trash_tracking

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install core package in editable mode
pip install -e packages/core/

# Install dev dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=packages/core/trash_tracking_core --cov-report=html

# Run specific test
pytest tests/test_tracker.py -v
```

### Code Quality

```bash
# Linting
flake8 packages/core/trash_tracking_core custom_components/trash_tracking

# Format code
black packages/core/trash_tracking_core custom_components/trash_tracking
isort packages/core/trash_tracking_core custom_components/trash_tracking

# Type checking
mypy packages/core/trash_tracking_core --ignore-missing-imports
```

---

## 📖 Documentation

- [Architecture Design](docs/architecture.md) - Technical architecture overview
- [Development Guide](DEVELOPMENT.md) - Development setup and guidelines
- [API Specification](docs/api-specification.md) - NTPC API documentation
- [Versioning Guide](docs/VERSIONING.md) - Release and versioning strategy

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- New Taipei City Environmental Protection Bureau for providing the public API
- Home Assistant community for the amazing platform
- All contributors who helped improve this integration

---

## 📮 Support

- **Issues**: [GitHub Issues](https://github.com/iml885203/trash_tracking/issues)
- **Discussions**: [GitHub Discussions](https://github.com/iml885203/trash_tracking/discussions)
- **Documentation**: [GitHub Wiki](https://github.com/iml885203/trash_tracking/wiki)

---

**Made with ❤️ for the Home Assistant community**
