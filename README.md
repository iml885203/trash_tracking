# 🚛 Trash Tracking System

[![GitHub release](https://img.shields.io/github/v/release/iml885203/trash_tracking)](https://github.com/iml885203/trash_tracking/releases)
[![License](https://img.shields.io/github/license/iml885203/trash_tracking)](LICENSE)
[![CI](https://github.com/iml885203/trash_tracking/actions/workflows/ci.yml/badge.svg)](https://github.com/iml885203/trash_tracking/actions)

Real-time garbage truck tracking and Home Assistant automation integration for New Taipei City, Taiwan.

## 📋 Overview

Track garbage trucks in real-time using the New Taipei City Environmental Protection Bureau API. Automatically trigger Home Assistant devices (lights, notifications, etc.) when trucks approach or pass your designated collection points.

### ✨ Key Features

- 🚛 **Real-time Tracking**: Monitor New Taipei City garbage truck locations
- 📍 **Custom Collection Points**: Set entry/exit collection points
- 🎯 **Multi-route Support**: Track multiple garbage truck routes
- ⏰ **Early Notification**: Configure advance notification (N stops ahead)
- 🏠 **Home Assistant Integration**: Seamless RESTful API integration
- 🐳 **Containerized Deployment**: Docker and Home Assistant Add-on support
- 🔧 **CLI Tool**: Command-line interface for real-time truck queries

### 🎬 Workflow

```
Truck approaching entry point → API status: nearby → HA automation → 💡 Light ON
Truck passing exit point → API status: idle → HA automation → 🌑 Light OFF
```

---

## 🚀 Quick Start

### Method 1️⃣: Home Assistant Add-on (Recommended)

**Easiest installation method** for all Home Assistant users.

#### Installation Steps

1. **Add Add-on Repository**
   - In Home Assistant: **Supervisor** → **Add-on Store**
   - Click top-right ⋮ → **Repositories**
   - Add: `https://github.com/iml885203/trash_tracking`
   - Click **Add**

2. **Install Add-on**
   - Find "**Trash Tracking**" in the Add-on Store
   - Click **Install**

3. **Configure Add-on**
   - Go to **Configuration** tab
   - Fill in your coordinates and collection point names (see below)
   - Click **Save**

4. **Start Add-on**
   - Go to **Info** tab
   - Click **Start**

5. **Setup Home Assistant Integration**
   - Refer to the **Documentation** tab in the Add-on
   - Or see [Complete User Guide](trash_tracking_addon/DOCS.md)

#### How to Find Collection Point Names?

**Using Add-on Built-in CLI Tool** (easiest):

```bash
# In Home Assistant Terminal add-on
docker exec -it addon_*_trash_tracking python3 cli.py --lat YOUR_LAT --lng YOUR_LNG
```

**Or use the Official Website**:
- Visit [New Taipei City Garbage Truck Tracker](https://crd-rubbish.epd.ntpc.gov.tw/)
- Enter your address to query collection point names

#### 📖 Detailed Documentation

- 📘 [Complete User Guide](trash_tracking_addon/DOCS.md) - Configuration examples, troubleshooting
- 📗 [Add-on Overview](trash_tracking_addon/README.md) - Add-on features
- 📙 [Quick Start Guide](QUICK_START_ADDON.md) - Publishing and installation

---

### Method 2️⃣: Docker Compose (Advanced Users)

For advanced users who want to manage containers themselves.

```bash
# 1. Clone repository
git clone https://github.com/iml885203/trash_tracking.git
cd trash_tracking

# 2. Edit configuration
cp config.example.yaml config.yaml
# Edit config.yaml with your coordinates and collection points

# 3. Start service
docker-compose up -d

# 4. View logs
docker-compose logs -f
```

Configuration example:

```yaml
location:
  lat: 25.018269
  lng: 121.471703

tracking:
  target_lines:
    - "C08 Afternoon Route"
  enter_point: "Minsheng Rd. Sec. 2, No. 80"
  exit_point: "Chenggong Rd. No. 23"
  trigger_mode: "arriving"
  approaching_threshold: 2
```

---

### Method 3️⃣: Python Direct Run (Developers)

For development/testing or environments without Docker.

```bash
# 1. Clone repository
git clone https://github.com/iml885203/trash_tracking.git
cd trash_tracking

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Edit configuration
cp config.example.yaml config.yaml
# Edit config.yaml

# 5. Start service
python3 app.py
```

---

## 🔌 Home Assistant Integration

Integration setup required in Home Assistant regardless of deployment method.

### Basic Setup

Edit `configuration.yaml`:

```yaml
# RESTful Sensor
sensor:
  - platform: rest
    name: "Garbage Truck Monitor"
    resource: "http://localhost:5000/api/trash/status"
    scan_interval: 90
    json_attributes:
      - reason
      - truck
      - timestamp
    value_template: "{{ value_json.status }}"

# Binary Sensor
binary_sensor:
  - platform: template
    sensors:
      garbage_truck_nearby:
        friendly_name: "Garbage Truck Nearby"
        value_template: "{{ is_state('sensor.garbage_truck_monitor', 'nearby') }}"
        device_class: presence

# Automation - Turn on light when truck arrives
automation:
  - alias: "Garbage Truck Arrived - Turn On Light"
    trigger:
      - platform: state
        entity_id: binary_sensor.garbage_truck_nearby
        to: 'on'
    action:
      - service: light.turn_on
        target:
          entity_id: light.notification_bulb  # Change to your light
        data:
          brightness: 255
          rgb_color: [255, 0, 0]

  - alias: "Garbage Truck Left - Turn Off Light"
    trigger:
      - platform: state
        entity_id: binary_sensor.garbage_truck_nearby
        to: 'off'
    action:
      - service: light.turn_off
        target:
          entity_id: light.notification_bulb
```

More examples: [trash_tracking_addon/DOCS.md](trash_tracking_addon/DOCS.md)

---

## 🖥️ CLI Command-Line Tool

Quick queries for nearby garbage trucks in real-time.

### Basic Usage

```bash
# Query trucks near specified coordinates
python3 cli.py --lat 25.018269 --lng 121.471703

# Specify query radius
python3 cli.py --lat 25.018269 --lng 121.471703 --radius 1500

# Show only next 5 collection points
python3 cli.py --lat 25.018269 --lng 121.471703 --next 5

# Filter specific route
python3 cli.py --lat 25.018269 --lng 121.471703 --line "C08 Afternoon Route"

# Show debug messages
python3 cli.py --lat 25.018269 --lng 121.471703 --debug
```

### Output Example

```
🔍 Query Location: (25.018269, 121.471703)
📏 Search Radius: 1000 meters

✅ Found 3 garbage trucks

================================================================================
🚛 Route Name: C08 Afternoon Route
   Vehicle No: KES-6950
   Current Stop: 10/69
   ✅ Status: 5 minutes ahead of schedule

📍 Next 10 Collection Points:
   1. [⏳ Scheduled 14:00 (Est. 13:55, 5min early)] Minsheng Rd. Sec. 2, No. 80
   2. [⏳ Scheduled 14:05 (Est. 14:00, 5min early)] Minsheng Rd. Sec. 2, No. 100
   3. [⏳ Scheduled 14:10 (Est. 14:05, 5min early)] Chenggong Rd. No. 23
   ...
```

### CLI Parameters

| Parameter | Required | Description | Default |
|-----------|----------|-------------|---------|
| `--lat` | ✅ | Query location latitude | - |
| `--lng` | ✅ | Query location longitude | - |
| `--radius` | ❌ | Query radius (meters) | 1000 |
| `--next` | ❌ | Number of upcoming collection points | 10 |
| `--line` | ❌ | Filter specific route name | - |
| `--debug` | ❌ | Show debug messages | false |

---

## 📡 API Endpoints

Service provides the following APIs after startup:

### `GET /health`

Health check endpoint.

**Response Example**:
```json
{
  "status": "ok",
  "timestamp": "2025-11-18T14:00:00+08:00",
  "config": {
    "enter_point": "Minsheng Rd. Sec. 2, No. 80",
    "exit_point": "Chenggong Rd. No. 23",
    "trigger_mode": "arriving"
  }
}
```

### `GET /api/trash/status`

Get garbage truck tracking status.

**Response Example (idle)**:
```json
{
  "status": "idle",
  "reason": "No garbage trucks nearby",
  "truck": null,
  "timestamp": "2025-11-18T14:00:00+08:00"
}
```

**Response Example (nearby)**:
```json
{
  "status": "nearby",
  "reason": "Garbage truck approaching entry collection point: Minsheng Rd. Sec. 2, No. 80",
  "truck": {
    "line_name": "C08 Afternoon Route",
    "car_no": "KES-6950",
    "current_rank": 10,
    "total_points": 69,
    "arrival_diff": -5,
    "enter_point": {
      "name": "Minsheng Rd. Sec. 2, No. 80",
      "rank": 12,
      "time": "14:00"
    },
    "exit_point": {
      "name": "Chenggong Rd. No. 23",
      "rank": 15,
      "time": "14:15"
    }
  },
  "timestamp": "2025-11-18T14:05:00+08:00"
}
```

### `POST /api/reset`

Reset tracker state (for testing).

Complete API Specification: [docs/api-specification.md](docs/api-specification.md)

---

## ⚙️ Configuration

### Complete Configuration Example

```yaml
# System settings
system:
  log_level: INFO  # DEBUG, INFO, WARNING, ERROR
  cache_enabled: false
  cache_ttl: 60

# Query location (your home coordinates)
location:
  lat: 25.018269
  lng: 121.471703

# Garbage truck tracking settings
tracking:
  # Specify routes to track (empty = track all routes)
  target_lines:
    - "C08 Afternoon Route"
    - "C15 Afternoon Route"

  # Entry collection point (light turns on)
  enter_point: "Minsheng Rd. Sec. 2, No. 80"

  # Exit collection point (light turns off)
  exit_point: "Chenggong Rd. No. 23"

  # Trigger mode
  # arriving: Advance notification (triggers before truck arrives)
  # arrived: Actual arrival (triggers when truck reaches point)
  trigger_mode: "arriving"

  # Advance notification threshold (arriving mode only)
  # 2 means trigger notification 2 stops before entry point
  approaching_threshold: 2

# API settings
api:
  ntpc:
    base_url: "https://crd-rubbish.epd.ntpc.gov.tw/WebAPI"
    timeout: 10
    retry_count: 3
    retry_delay: 2

  server:
    host: "0.0.0.0"
    port: 5000
    debug: false
```

### Trigger Mode Explanation

#### `arriving` Mode (Recommended)

Advance notification, time to prepare garbage.

```yaml
trigger_mode: "arriving"
approaching_threshold: 2  # Notify 2 stops in advance
```

**Example**:
- Entry point: Minsheng Rd. Sec. 2, No. 80 (Stop #12)
- Truck currently at Stop #10
- 2 stops until entry point → **Trigger notification** ✅

#### `arrived` Mode

Notification only when truck arrives, more urgent.

```yaml
trigger_mode: "arrived"
approaching_threshold: 0  # This parameter is ignored
```

---

## 🏗️ Project Architecture

```
trash_tracking/
├── src/                        # Core source code
│   ├── api/                    # API related
│   │   ├── client.py          # NTPC API client
│   │   └── routes.py          # Flask API routes
│   ├── core/                   # Core logic
│   │   ├── config.py          # Configuration management
│   │   ├── logger.py          # Logging system
│   │   ├── point_matcher.py  # Collection point matching logic
│   │   └── state_manager.py  # State management
│   └── models/                 # Data models
│       ├── point.py           # Collection point model
│       └── truck.py           # Garbage truck model
├── tests/                      # Test suite
├── docs/                       # Documentation
├── trash_tracking_addon/       # Home Assistant Add-on package
├── app.py                      # Flask application entry point
├── cli.py                      # CLI tool
├── config.yaml                 # Configuration file example
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker image
└── docker-compose.yml          # Docker Compose configuration
```

Complete architecture: [docs/architecture.md](docs/architecture.md)

---

## 🧪 Testing

Project includes comprehensive test suite (91 tests, ~70% coverage).

### Run Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/test_point_matcher.py -v
```

### Code Quality Checks

```bash
# Linting
flake8 src/ tests/

# Code formatting
black src/ tests/
isort src/ tests/

# Type checking
mypy src/

# Security scan
bandit -r src/
safety check
```

Detailed CI/CD Setup: [docs/CI_CD_SETUP.md](docs/CI_CD_SETUP.md)

---

## 📚 Documentation

### User Documentation
- 📘 [Complete User Guide](trash_tracking_addon/DOCS.md) - **Recommended Reading**
- 📗 [Add-on Overview](trash_tracking_addon/README.md)
- 📙 [Quick Start Guide](QUICK_START_ADDON.md)
- 📕 [Installation & Publishing Guide](docs/ADD_ON_INSTALLATION.md)

### Developer Documentation
- 🔵 [Project Architecture](docs/architecture.md)
- 🔵 [API Specification](docs/api-specification.md)
- 🔵 [Requirements](docs/requirements.md)
- 🔵 [CI/CD Setup](docs/CI_CD_SETUP.md)

---

## 🤝 Contributing

Pull requests and issues are welcome!

### Contribution Guidelines

1. Fork the project
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

### Development Setup

```bash
# Clone repository
git clone https://github.com/iml885203/trash_tracking.git
cd trash_tracking

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run code checks
flake8 src/ tests/
black --check src/ tests/
mypy src/
```

---

## 🐛 Issue Reporting

If you encounter problems:
1. Check [Issue List](https://github.com/iml885203/trash_tracking/issues)
2. Create new Issue with:
   - Home Assistant version (if using Add-on)
   - Error messages and logs
   - Configuration (remove sensitive data)

---

## 📄 License

This project is licensed under MIT License - see [LICENSE](LICENSE) file

---

## 🙏 Acknowledgments

- New Taipei City Environmental Protection Bureau for the garbage truck API
- Home Assistant community
- All contributors

---

## 📞 Contact

- GitHub: [@iml885203](https://github.com/iml885203)
- Project: [trash_tracking](https://github.com/iml885203/trash_tracking)
- Issues: [Report Issues](https://github.com/iml885203/trash_tracking/issues)

---

**⭐ Star this project if you find it helpful!**
