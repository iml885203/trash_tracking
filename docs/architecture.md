# Trash Tracking System - Architecture Design

## Document Overview

This document describes the technical architecture of the Trash Tracking Home Assistant integration, including module design, data flow, and key design patterns.

---

## 1. System Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Home Assistant                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Integration: Trash Tracking                           │ │
│  │  • Config Flow (Setup Wizard)                          │ │
│  │  • Coordinator (Data Updates)                          │ │
│  │  • Binary Sensor (nearby/idle)                         │ │
│  │  • Sensor (truck info)                                 │ │
│  └─────────────────────┬──────────────────────────────────┘ │
│                        │                                     │
│  ┌─────────────────────▼──────────────────────────────────┐ │
│  │  User Automations                                      │ │
│  │  • Truck nearby → Light ON                             │ │
│  │  • Truck left → Light OFF                              │ │
│  │  • Notifications, TTS, etc.                            │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
                          │
                          │ Embedded trash_tracking_core
                          ▼
┌─────────────────────────────────────────────────────────────┐
│           Trash Tracking Core (Embedded Package)            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Business Logic Layer                                  │ │
│  │  • Tracker: Track truck status                         │ │
│  │  • StateManager: Manage idle/nearby states             │ │
│  │  │  PointMatcher: Match collection points              │ │
│  │  • RouteAnalyzer: Analyze and recommend routes         │ │
│  └─────────────────────┬──────────────────────────────────┘ │
│                        │                                     │
│  ┌─────────────────────▼──────────────────────────────────┐ │
│  │  Data Access Layer                                     │ │
│  │  • NTPCApiClient: NTPC API client                      │ │
│  │  • Geocoder: Address → Coordinates conversion          │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTPS
                          ▼
┌─────────────────────────────────────────────────────────────┐
│   New Taipei City Environmental Protection Bureau API      │
│      https://crd-rubbish.epd.ntpc.gov.tw/WebAPI            │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Integration Framework** | Home Assistant Core | Native integration platform |
| **Programming Language** | Python 3.11+ | HA ecosystem compatibility |
| **HTTP Client** | requests | API communication |
| **Data Coordination** | DataUpdateCoordinator | Efficient data updates |
| **Configuration** | Config Flow | User-friendly setup wizard |
| **Geocoding** | Multiple APIs | Taiwan address → GPS conversion |
| **Timezone** | pytz | Taiwan timezone handling |

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
│       │   └── truck_line.py         # Truck route model
│       ├── core/                      # Business logic
│       │   ├── tracker.py            # Main tracking logic
│       │   ├── state_manager.py      # State machine
│       │   └── point_matcher.py      # Point matching logic
│       └── utils/                     # Utilities
│           ├── geocoding.py          # Address geocoding
│           ├── route_analyzer.py     # Route analysis
│           └── logger.py             # Logging utilities
├── custom_components/                 # Home Assistant Integration
│   └── trash_tracking/
│       ├── trash_tracking_core/      # Embedded core (auto-sync)
│       ├── __init__.py               # Integration setup
│       ├── config_flow.py            # Setup wizard
│       ├── coordinator.py            # Data coordinator
│       ├── sensor.py                 # Sensor entities
│       ├── binary_sensor.py          # Binary sensor entities
│       ├── const.py                  # Constants
│       └── manifest.json             # Integration metadata
├── apps/cli/                          # CLI tool (optional)
└── tests/                             # Unit tests
```

### 2.2 Core Modules

#### 2.2.1 Integration Layer (`custom_components/trash_tracking/`)

**`__init__.py`** - Integration Entry Point
- Sets up the integration when added to HA
- Creates and stores the coordinator
- Forwards setup to sensor platforms

**`config_flow.py`** - Setup Wizard
- Multi-step configuration flow:
  1. Address input and geocoding
  2. Route discovery and selection
  3. Collection point configuration
  4. Advanced settings (trigger mode, threshold)
- Validates user input
- Provides route recommendations

**`coordinator.py`** - Data Update Coordinator
- Extends `DataUpdateCoordinator`
- Manages periodic data updates (90s interval)
- Calls core `Tracker` for status updates
- Handles API errors gracefully
- Notifies sensors when data changes

**`binary_sensor.py`** - Binary Sensor Platform
- Provides `nearby` state (ON/OFF)
- Used in automations for triggering
- Rich attributes (current point, distance, etc.)

**`sensor.py`** - Sensor Platform
- Provides detailed truck information
- JSON attributes with full truck data

#### 2.2.2 Core Business Logic (`trash_tracking_core/core/`)

**`tracker.py`** - Main Tracking Logic
```python
class TruckTracker:
    """
    Main tracker that orchestrates:
    - Fetching truck data from API
    - Matching against collection points
    - Determining truck status (idle/nearby)
    """

    def get_status() -> dict:
        """Returns current tracking status"""
```

**`state_manager.py`** - State Machine
```python
class StateManager:
    """
    Manages state transitions:
    - idle → nearby (truck approaching)
    - nearby → idle (truck left)

    Prevents state flickering with hysteresis
    """
```

**`point_matcher.py`** - Collection Point Matching
```python
class PointMatcher:
    """
    Matches trucks against collection points:
    - Finds if truck is at/near entry point
    - Checks if truck passed exit point
    - Supports two trigger modes:
      - arriving: N stops before entry
      - arrived: exactly at entry point
    """
```

#### 2.2.3 Data Access Layer (`trash_tracking_core/clients/`)

**`ntpc_api.py`** - NTPC API Client
```python
class NTPCApiClient:
    """
    New Taipei City API client:
    - POST to GetAroundPoints endpoint
    - Filters by time and day of week
    - Returns list of TruckLine objects
    - Handles SSL/connection errors
    """
```

#### 2.2.4 Utilities (`trash_tracking_core/utils/`)

**`geocoding.py`** - Address Geocoding
```python
class Geocoder:
    """
    Multi-provider geocoding:
    1. NLSC (National Land Surveying)
    2. Nominatim (OpenStreetMap)
    3. TGOS (Taiwan Geographic Service)

    Handles TWD97 → WGS84 conversion
    """
```

**`route_analyzer.py`** - Route Analysis
```python
class RouteAnalyzer:
    """
    Analyzes garbage truck routes:
    - Finds nearest collection points
    - Suggests entry/exit points
    - Ranks routes by distance
    """
```

---

## 3. Data Flow

### 3.1 Setup Flow (Config Flow)

```
User enters address
    │
    ▼
Geocoder.address_to_coordinates()
    │
    ▼
NTPCApiClient.get_around_points(lat, lng)
    │
    ▼
RouteAnalyzer.analyze_all_routes()
    │
    ▼
User selects route
    │
    ▼
User configures points & settings
    │
    ▼
Config entry created
```

### 3.2 Update Flow (Coordinator)

```
Coordinator timer triggers (every 90s)
    │
    ▼
Coordinator.async_update_data()
    │
    ▼
Tracker.get_status()
    │
    ├─▶ NTPCApiClient.get_around_points()
    │
    ├─▶ PointMatcher.find_matching_truck()
    │
    └─▶ StateManager.update_state()
    │
    ▼
Return status dict
    │
    ▼
Sensors update their state
    │
    ▼
Automations trigger (if state changed)
```

### 3.3 State Transition Flow

```
Initial State: idle
    │
    ▼
Truck approaching entry point
    │
    ▼
PointMatcher detects (rank check)
    │
    ▼
StateManager → nearby
    │
    ▼
Binary Sensor: ON
    │
    ▼
Automation triggers (light on)
    │
    ▼
Truck passes exit point
    │
    ▼
PointMatcher detects
    │
    ▼
StateManager → idle
    │
    ▼
Binary Sensor: OFF
    │
    ▼
Automation triggers (light off)
```

---

## 4. Key Design Patterns

### 4.1 State Machine Pattern

The system uses a simple state machine with two states:

- **idle**: No truck nearby (default state)
- **nearby**: Truck is approaching or at collection point

State transitions are managed by `StateManager` with hysteresis to prevent flickering.

### 4.2 Strategy Pattern (Trigger Modes)

Two trigger strategies are supported:

**Arriving Mode**:
```python
# Triggers N stops before entry point
if current_rank <= (enter_rank - threshold):
    state = "nearby"
```

**Arrived Mode**:
```python
# Triggers exactly at entry point
if current_rank == enter_rank:
    state = "nearby"
```

### 4.3 Coordinator Pattern

Uses Home Assistant's `DataUpdateCoordinator`:
- Centralized data fetching
- Automatic retry on errors
- Efficient sensor updates
- Prevents duplicate API calls

### 4.4 Embedded Package Pattern

The `trash_tracking_core` package is embedded in the integration:
- Shared code between integration and CLI
- Easy to update (sync script)
- No external dependencies for users

---

## 5. Data Models

### 5.1 Point Model

```python
@dataclass
class Point:
    point_name: str      # "Minsheng Rd. Sec. 2, No. 80"
    latitude: float      # 25.018269
    longitude: float     # 121.471703
    rank: int           # 12 (order in route)
    time: str           # "18:30" (scheduled time)
    distance_meters: float  # Distance from user location
```

### 5.2 TruckLine Model

```python
@dataclass
class TruckLine:
    car_no: str         # "ABC-1234"
    line_name: str      # "C08 Afternoon Route"
    points: List[Point]  # Collection points
    time_type: str      # "下午" (afternoon)
    week: int           # 1 (Monday)
```

### 5.3 Tracker Status

```python
{
    "status": "nearby",  # or "idle"
    "reason": "Truck at entry point",
    "truck": {
        "car_no": "ABC-1234",
        "line_name": "C08 Afternoon Route",
        "current_point": "Minsheng Rd. Sec. 2, No. 80",
        "current_rank": 12,
        "total_points": 69,
        "distance_meters": 45.2
    },
    "timestamp": "2025-11-23T14:30:00"
}
```

---

## 6. Configuration

### 6.1 Config Entry Data

Stored in Home Assistant's config entry:

```python
{
    "address": "新北市板橋區民生路二段80號",
    "latitude": 25.018269,
    "longitude": 121.471703,
    "route_selection": {
        "vehicle_number": "ABC-1234",
        "route_names": ["C08 Afternoon Route"]
    },
    "enter_point": "Minsheng Rd. Sec. 2, No. 80",
    "exit_point": "Chenggong Rd. No. 23",
    "trigger_mode": "arriving",
    "approaching_threshold": 2
}
```

---

## 7. Error Handling

### 7.1 API Errors

- **Connection errors**: Logged, coordinator retries
- **SSL errors**: Logged, SSL verification disabled (NTPC API issue)
- **Timeout**: 10s timeout, coordinator handles gracefully

### 7.2 Geocoding Errors

- **Invalid address**: Show error in config flow
- **No results**: Try multiple geocoding providers
- **Coordinate conversion**: Fallback to direct WGS84

### 7.3 State Errors

- **No trucks found**: State remains idle
- **Invalid points**: Logged, no state change
- **Data corruption**: Coordinator catches exceptions

---

## 8. Performance Considerations

### 8.1 Update Frequency

- Default: 90 seconds
- Configurable via integration options
- Balance between freshness and API load

### 8.2 Caching

- Coordinator caches data between updates
- Sensors read from coordinator cache
- No redundant API calls

### 8.3 Async Operations

- All I/O operations are async
- Non-blocking API calls
- HA executor used for blocking operations (geocoding)

---

## 9. Security

### 9.1 API Security

- HTTPS communication
- SSL verification (disabled for NTPC API due to certificate issues)
- No authentication required (public API)

### 9.2 Data Privacy

- No user data sent to external services (except coordinates for geocoding)
- All tracking data stays local in Home Assistant
- No cloud dependencies

---

## 10. Testing Strategy

### 10.1 Unit Tests

- Core business logic (pytest)
- Mock external API calls
- Test state machine transitions
- Test point matching logic

### 10.2 Integration Tests

- Not yet implemented
- Would test actual HA integration
- Require HA test environment

---

## 11. Future Enhancements

Potential improvements:

1. **Multiple Routes**: Track multiple routes simultaneously
2. **Historical Data**: Store and analyze truck punctuality
3. **Predictive Alerts**: ML-based arrival time prediction
4. **Map View**: Custom Lovelace card with map
5. **Notification Templates**: Pre-built notification examples
6. **Mobile App**: Dedicated mobile app for route tracking

---

## 12. References

- [Home Assistant Integration Development](https://developers.home-assistant.io/)
- [NTPC Garbage Truck API](https://crd-rubbish.epd.ntpc.gov.tw/)
- [DataUpdateCoordinator Documentation](https://developers.home-assistant.io/docs/integration_fetching_data)
- [Config Flow Best Practices](https://developers.home-assistant.io/docs/config_entries_config_flow_handler)
