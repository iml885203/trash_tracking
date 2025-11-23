# Garbage Truck Tracking System - Architecture Design Document

## Document Overview

This document describes the technical architecture, module design, data flow, and deployment strategy of the garbage truck tracking system.

---

## 1. System Architecture Overview

### 1.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Home Assistant                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  RESTful Sensor (polls every 90 seconds)               │ │
│  │  • sensor.garbage_truck_monitor                        │ │
│  │  • binary_sensor.garbage_truck_nearby                  │ │
│  └─────────────────────┬──────────────────────────────────┘ │
│                        │                                     │
│  ┌─────────────────────▼──────────────────────────────────┐ │
│  │  Automation                                            │ │
│  │  • Truck arrives → Light turns on                      │ │
│  │  • Truck leaves → Light turns off                      │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP GET /api/trash/status
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Flask Application (Python 3.11+)               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  API Layer (Flask)                                     │ │
│  │  • GET /api/trash/status                               │ │
│  │  • GET /health                                         │ │
│  └─────────────────────┬──────────────────────────────────┘ │
│                        │                                     │
│  ┌─────────────────────▼──────────────────────────────────┐ │
│  │  Business Logic Layer                                  │ │
│  │  • TruckTracker: Truck tracking logic                  │ │
│  │  • StateManager: State management (idle/nearby)        │ │
│  │  • PointMatcher: Collection point matching logic       │ │
│  └─────────────────────┬──────────────────────────────────┘ │
│                        │                                     │
│  ┌─────────────────────▼──────────────────────────────────┐ │
│  │  Data Access Layer                                     │ │
│  │  • APIClient: New Taipei City API client               │ │
│  │  • ConfigManager: Configuration management             │ │
│  │  • Cache: Caching mechanism (optional)                 │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP POST
                          ▼
┌─────────────────────────────────────────────────────────────┐
│          New Taipei City Garbage Truck API (External)       │
│      https://crd-rubbish.epd.ntpc.gov.tw/WebAPI            │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

| Layer | Technology | Rationale |
|------|---------|------|
| **Web Framework** | Flask 3.0+ | Lightweight, easy to develop, RESTful-friendly |
| **Programming Language** | Python 3.11+ | Home Assistant ecosystem, rich libraries |
| **HTTP Client** | requests | Standard, stable, easy to use |
| **Configuration Management** | PyYAML | YAML format is human-friendly, easy to edit |
| **Logging** | Python logging | Standard library, no extra dependencies |
| **Deployment** | Docker (optional) | Cross-platform, easy to deploy to HA OS |
| **Timezone Handling** | pytz | Correctly handles Taiwan timezone |

---

## 2. Module Design

### 2.1 Project Structure

```
trash_tracking/
├── packages/core/                     # Shared core package
│   └── trash_tracking_core/
│       ├── clients/                   # API clients
│       │   └── ntpc_api.py           # NTPC API client
│       ├── models/                    # Data models
│       │   ├── point.py              # Collection point model
│       │   └── truck.py              # Truck line model
│       ├── core/                      # Business logic
│       │   ├── tracker.py            # Truck tracking logic
│       │   ├── state_manager.py      # State management
│       │   └── point_matcher.py      # Point matching logic
│       └── utils/                     # Utilities
│           ├── config.py             # Configuration management
│           ├── geocoding.py          # Geocoding service
│           └── logger.py             # Logging utilities
│
├── apps/addon/                        # Home Assistant Add-on
│   ├── app.py                        # Flask entry point
│   ├── config.yaml                   # User configuration
│   ├── Dockerfile                    # Docker config
│   └── addon/
│       ├── api/                      # API layer
│       │   └── routes.py            # Flask routes
│       └── use_cases/                # Setup wizard logic
│
├── apps/cli/                          # CLI tool
│   └── cli.py                        # CLI entry point
│
├── custom_components/                 # Home Assistant Integration
│   └── trash_tracking/
│       ├── __init__.py               # Component initialization
│       ├── config_flow.py            # UI config flow
│       ├── coordinator.py            # Data coordinator
│       ├── sensor.py                 # Sensor entities
│       ├── manifest.json             # Integration manifest
│       └── trash_tracking_core/      # Embedded core package
│
├── features/                          # BDD tests (Behave)
├── tests/                             # Unit tests (pytest)
├── requirements.txt                   # Dependencies
└── README.md                          # Documentation
```

### 2.2 Core Module Descriptions

#### 2.2.1 API Layer (`addon/api/routes.py`)

**Responsibility**: Handle HTTP requests and responses

```python
from flask import Flask, jsonify
from src.core.tracker import TruckTracker

app = Flask(__name__)
tracker = TruckTracker()

@app.route('/api/trash/status', methods=['GET'])
def get_status():
    """Get garbage truck status"""
    status = tracker.get_current_status()
    return jsonify(status)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok"})
```

#### 2.2.2 Truck Tracker (`trash_tracking_core/core/tracker.py`)

**Responsibility**: Coordinate modules and implement main tracking logic

```python
class TruckTracker:
    """Garbage truck tracker"""

    def __init__(self, config: dict):
        self.config = config
        self.api_client = NTPCApiClient()
        self.state_manager = StateManager()
        self.point_matcher = PointMatcher(
            enter_point=config['enter_point'],
            exit_point=config['exit_point']
        )

    def get_current_status(self) -> dict:
        """
        Get current garbage truck status

        Returns:
            dict: Status information including status, reason, truck, timestamp
        """
        # 1. Call New Taipei City API
        api_data = self.api_client.get_around_points(
            lat=self.config['lat'],
            lng=self.config['lng']
        )

        # 2. Filter target routes
        target_lines = self._filter_target_lines(api_data)

        # 3. Check collection point status for each route
        for line in target_lines:
            match_result = self.point_matcher.check_line(line)

            if match_result['should_trigger']:
                # Update state
                new_state = match_result['new_state']
                self.state_manager.update_state(new_state, line)
                break

        # 4. Return current status
        return self.state_manager.get_status_response()
```

#### 2.2.3 State Manager (`trash_tracking_core/core/state_manager.py`)

**Responsibility**: Manage system state (idle ↔ nearby)

```python
from enum import Enum
from datetime import datetime

class TruckState(Enum):
    IDLE = "idle"
    NEARBY = "nearby"

class StateManager:
    """State manager"""

    def __init__(self):
        self.current_state = TruckState.IDLE
        self.current_truck = None
        self.last_update = None

    def update_state(self, new_state: TruckState, truck_data: dict = None):
        """
        Update system state

        Args:
            new_state: New state
            truck_data: Truck data (required when state is nearby)
        """
        if self.current_state != new_state:
            self.current_state = new_state
            self.current_truck = truck_data
            self.last_update = datetime.now()

    def get_status_response(self) -> dict:
        """Generate API response"""
        return {
            "status": self.current_state.value,
            "reason": self._get_reason(),
            "truck": self.current_truck,
            "timestamp": self.last_update.isoformat()
        }
```

#### 2.2.4 Point Matcher (`trash_tracking_core/core/point_matcher.py`)

**Responsibility**: Determine if truck has reached entry/exit collection points

```python
class PointMatcher:
    """Collection point matcher"""

    def __init__(self, enter_point: str, exit_point: str,
                 trigger_mode: str = 'arriving', threshold: int = 2):
        self.enter_point = enter_point
        self.exit_point = exit_point
        self.trigger_mode = trigger_mode
        self.threshold = threshold

    def check_line(self, line_data: dict) -> dict:
        """
        Check if route should trigger state change

        Args:
            line_data: Route data returned by API

        Returns:
            dict: {
                'should_trigger': bool,
                'new_state': TruckState,
                'reason': str
            }
        """
        current_rank = line_data['ArrivalRank']
        points = line_data['Point']

        # Find entry and exit points
        enter_point_data = self._find_point(points, self.enter_point)
        exit_point_data = self._find_point(points, self.exit_point)

        if not enter_point_data or not exit_point_data:
            return {'should_trigger': False}

        # Check if approaching entry point
        if self._is_approaching_enter_point(current_rank, enter_point_data):
            return {
                'should_trigger': True,
                'new_state': TruckState.NEARBY,
                'reason': f'Truck approaching {self.enter_point}'
            }

        # Check if passed exit point
        if self._has_passed_exit_point(exit_point_data):
            return {
                'should_trigger': True,
                'new_state': TruckState.IDLE,
                'reason': f'Truck passed {self.exit_point}'
            }

        return {'should_trigger': False}

    def _is_approaching_enter_point(self, current_rank: int,
                                     enter_point: dict) -> bool:
        """Determine if approaching entry point"""
        enter_rank = enter_point['PointRank']
        distance = enter_rank - current_rank

        if self.trigger_mode == 'arriving':
            return 0 <= distance <= self.threshold
        else:  # arrived
            return enter_point['Arrival'] != ""

    def _has_passed_exit_point(self, exit_point: dict) -> bool:
        """Determine if passed exit point"""
        return exit_point['Arrival'] != ""
```

#### 2.2.5 NTPC API Client (`trash_tracking_core/clients/ntpc_api.py`)

**Responsibility**: Encapsulate New Taipei City API call logic

```python
import requests
from typing import Optional

class NTPCApiClient:
    """New Taipei City garbage truck API client"""

    BASE_URL = "https://crd-rubbish.epd.ntpc.gov.tw/WebAPI"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()

    def get_around_points(self, lat: float, lng: float) -> Optional[dict]:
        """
        Query nearby garbage trucks

        Args:
            lat: Latitude
            lng: Longitude

        Returns:
            dict: API response data, None on failure
        """
        url = f"{self.BASE_URL}/GetAroundPoints"
        payload = {"lat": lat, "lng": lng}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            response = self.session.post(
                url,
                data=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            # Log error and return None
            logger.error(f"API request failed: {e}")
            return None
```

---

## 3. Data Flow

### 3.1 State Transition Flow

```
                        ┌──────────────┐
                        │ System Start │
                        └──────┬───────┘
                               │
                               ▼
                        ┌──────────────┐
                   ┌────│  idle State  │◄────┐
                   │    │ (light off)  │      │
                   │    └──────┬───────┘      │
                   │           │              │
                   │           │ HA polls     │
                   │           │ every 90s    │
                   │           ▼              │
                   │    ┌──────────────┐      │
                   │    │ Query NTPC   │      │
                   │    │ API          │      │
                   │    └──────┬───────┘      │
                   │           │              │
                   │           ▼              │
                   │    ┌──────────────┐      │
                   │    │ Check Entry  │      │
                   │    │ Point        │      │
                   │    └──────┬───────┘      │
                   │           │              │
                   │           │ Yes          │
                   │           ▼              │
                   │    ┌──────────────┐      │
                   │    │ nearby State │      │
                   │    │ (light on)   │      │
                   │    └──────┬───────┘      │
                   │           │              │
                   │           │ Continue     │
                   │           │ polling      │
                   │           ▼              │
                   │    ┌──────────────┐      │
                   │    │ Check Exit   │      │
                   │    │ Point        │      │
                   │    └──────┬───────┘      │
                   │           │              │
                   │           │ Yes          │
                   └───────────┴──────────────┘
```

### 3.2 API Call Flow

```
Home Assistant              Flask App              NTPC API
     │                         │                      │
     │  GET /api/trash/status  │                      │
     ├────────────────────────>│                      │
     │                         │                      │
     │                         │  POST /GetAroundPoints
     │                         ├─────────────────────>│
     │                         │                      │
     │                         │   JSON Response      │
     │                         │<─────────────────────┤
     │                         │                      │
     │                         │ Processing logic:    │
     │                         │ 1. Filter routes     │
     │                         │ 2. Match points      │
     │                         │ 3. Update state      │
     │                         │                      │
     │   JSON Response         │                      │
     │<────────────────────────┤                      │
     │                         │                      │
```

---

## 4. Configuration File Design

### 4.1 config.yaml Structure

```yaml
# System settings
system:
  log_level: INFO           # Log level: DEBUG, INFO, WARNING, ERROR
  cache_enabled: false      # Enable caching (future feature)
  cache_ttl: 60            # Cache TTL (seconds)

# Query location (your home coordinates)
location:
  lat: 25.005193869072745
  lng: 121.5099557021958

# Garbage truck tracking settings
tracking:
  # Specify target routes (empty array = track all routes)
  target_lines:
    - "District 3 Evening 9"
    # - "District 3 Evening 11"

  # Entry point
  enter_point: "Shuiyuan St. Lane 36 Intersection"

  # Exit point
  exit_point: "Shuiyuan St. No. 28"

  # Trigger mode
  # arriving: Trigger when approaching entry point
  # arrived: Trigger when arrived at entry point
  trigger_mode: "arriving"

  # Number of stops ahead for advance notification (only when trigger_mode=arriving)
  approaching_threshold: 2

# API settings
api:
  # New Taipei City API settings
  ntpc:
    base_url: "https://crd-rubbish.epd.ntpc.gov.tw/WebAPI"
    timeout: 10             # Request timeout (seconds)
    retry_count: 3          # Number of retries
    retry_delay: 2          # Retry delay (seconds)

  # Flask server settings
  server:
    host: "0.0.0.0"
    port: 5000
    debug: false

# Home Assistant integration settings (documentation reference)
home_assistant:
  scan_interval: 90         # HA polling interval (seconds)
  light_entity_id: "light.notification_bulb"  # Light entity ID to control
```

### 4.2 Configuration File Validation

The system validates the following on startup:
- Required fields exist
- Coordinate format is correct
- Entry and exit points are not the same
- trigger_mode must be 'arriving' or 'arrived'

---

## 5. Error Handling Strategy

### 5.1 External API Errors

| Error Type | Handling Strategy |
|---------|---------|
| Connection timeout | Retry 3 times, maintain last state on failure |
| HTTP 4xx | Log error, return error message to HA |
| HTTP 5xx | Log error, maintain last state |
| JSON parsing failure | Log error, maintain last state |

### 5.2 Internal Logic Errors

| Error Type | Handling Strategy |
|---------|---------|
| Collection point not found | Log warning, return idle state |
| Configuration file error | Throw exception on startup, refuse to start |
| State anomaly | Reset to idle state |

---

## 6. Deployment Architecture

### 6.1 Docker Deployment

#### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Expose port
EXPOSE 5000

# Start application
CMD ["python", "app.py"]
```

#### docker-compose.yml
```yaml
version: '3.8'

services:
  trash_light:
    build: .
    container_name: trash_light
    ports:
      - "5000:5000"
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./logs:/app/logs
    environment:
      - TZ=Asia/Taipei
    restart: unless-stopped
```

### 6.2 Home Assistant Add-on Deployment

The project can be packaged as a Home Assistant Add-on for direct installation via the Add-on Store.

#### config.json (Add-on configuration)
```json
{
  "name": "Garbage Truck Light",
  "version": "1.0.0",
  "slug": "garbage_truck_light",
  "description": "New Taipei City garbage truck tracking and light control",
  "arch": ["armhf", "armv7", "aarch64", "amd64", "i386"],
  "startup": "application",
  "boot": "auto",
  "ports": {
    "5000/tcp": 5000
  },
  "options": {
    "location": {
      "lat": 25.005193869072745,
      "lng": 121.5099557021958
    },
    "tracking": {
      "enter_point": "Shuiyuan St. Lane 36 Intersection",
      "exit_point": "Shuiyuan St. No. 28"
    }
  },
  "schema": {
    "location": {
      "lat": "float",
      "lng": "float"
    },
    "tracking": {
      "target_lines": ["str?"],
      "enter_point": "str",
      "exit_point": "str",
      "trigger_mode": "list(arriving|arrived)?",
      "approaching_threshold": "int?"
    }
  }
}
```

---

## 7. Performance Considerations

### 7.1 Performance Metrics

| Metric | Target | Measurement Method |
|------|--------|---------|
| API response time | < 2 seconds | Using Flask built-in timing |
| Memory usage | < 512 MB | Docker stats monitoring |
| CPU usage | < 10% | Docker stats monitoring |

### 7.2 Optimization Strategies

1. **Reduce API calls**:
   - HA polling interval set to 90 seconds (adjustable)
   - Avoid redundant queries for the same time period

2. **Caching mechanism** (future feature):
   - Cache NTPC API responses for 60 seconds
   - Reduce load on external API

3. **Connection pooling**:
   - Use `requests.Session()` to reuse TCP connections

---

## 8. Security Considerations

### 8.1 Data Privacy
- User coordinates are only used for API queries, not logged or sent elsewhere
- Logs do not contain sensitive information

### 8.2 API Security
- Restrict API to listen on localhost only (unless remote access needed)
- Future: add API key authentication mechanism

### 8.3 Dependency Management
- Regularly update Python packages to patch security vulnerabilities
- Use `pip-audit` to scan for known vulnerabilities

---

## 9. Monitoring and Logging

### 9.1 Log Format

```
2025-11-17 21:00:00 [INFO] TruckTracker: Starting garbage truck status query
2025-11-17 21:00:01 [INFO] NTPCApiClient: API request successful (200)
2025-11-17 21:00:01 [INFO] PointMatcher: Found route "District 3 Evening 9"
2025-11-17 21:00:01 [INFO] PointMatcher: Truck approaching entry point "Shuiyuan St. Lane 36 Intersection"
2025-11-17 21:00:01 [INFO] StateManager: State change: idle -> nearby
2025-11-17 21:00:01 [INFO] Flask: 200 GET /api/trash/status
```

### 9.2 Health Check

Provides `/health` endpoint for monitoring systems:

```bash
curl http://localhost:5000/health
# Response: {"status": "ok", "timestamp": "2025-11-17T21:00:00"}
```

---

## 10. Extensibility Design

### 10.1 Multi-User Support

Future extension to support multiple users with independent configurations:

```python
class MultiUserTracker:
    def __init__(self):
        self.trackers = {}  # user_id -> TruckTracker

    def get_status(self, user_id: str) -> dict:
        if user_id not in self.trackers:
            self.trackers[user_id] = self._create_tracker(user_id)
        return self.trackers[user_id].get_current_status()
```

### 10.2 Support for Other Cities

Architecture design supports garbage truck APIs from other cities:

```python
class APIClientFactory:
    @staticmethod
    def create(city: str):
        if city == "ntpc":
            return NTPCApiClient()
        elif city == "taipei":
            return TaipeiApiClient()
        # ... other cities
```

---

## 11. Testing Strategy

### 11.1 Unit Testing

- Test PointMatcher logic
- Test StateManager state transitions
- Mock external API calls

### 11.2 Integration Testing

- Test Flask API endpoints
- Test complete data flow

### 11.3 End-to-End Testing

- Test with real New Taipei City API
- Verify Home Assistant integration

---

## 12. Known Limitations and Future Improvements

### 12.1 Known Limitations

1. **Single-threaded design**: Does not support multi-user concurrency
2. **No persistence**: State lost after system restart
3. **No authentication**: API has no authentication implemented
4. **External API dependency**: Cannot operate if NTPC API is down

### 12.2 Future Improvements

1. **Add database**: Store historical records for statistical analysis
2. **WebSocket push**: Actively push state changes to HA
3. **Web management interface**: Provide graphical configuration interface
4. **Map visualization**: Display real-time truck location
5. **Multiple notification channels**: Support LINE, Telegram notifications

---

**Document Version**: v1.0
**Last Updated**: 2025-11-17
**Maintainer**: Logan
**Project Name**: trash_light
