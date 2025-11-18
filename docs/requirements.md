# Garbage Truck Dynamic Detection System - Requirements Specification

## Project Overview

### Purpose
Develop a garbage truck dynamic detection system to detect whether garbage trucks arrive near designated collection points, and automatically control light on/off through Home Assistant automation to remind users of garbage truck arrival.

### Objectives
- Real-time tracking of garbage truck location
- Light turns on when garbage truck passes "entry collection point"
- Light turns off when garbage truck passes "exit collection point"
- Deep integration with Home Assistant

---

## Functional Requirements

### FR-1: Garbage Truck Location Tracking

**Description**: The system needs to periodically query the New Taipei City Garbage Truck API to obtain real-time garbage truck location information.

**Requirement Details**:
- API Endpoint: `https://crd-rubbish.epd.ntpc.gov.tw/WebAPI/GetAroundPoints`
- Query Frequency: Every 1-2 minutes
- Input Parameters: User's home coordinates (latitude/longitude)
- Output Data: Nearby garbage truck routes, stops, real-time location

### FR-2: Collection Point Status Determination

**Description**: The system needs to track whether garbage trucks pass through user-specified "entry collection point" and "exit collection point".

**Determination Logic**:

#### 2.1 Entry Collection Point Trigger
- **Condition**: Garbage truck arrives at or is approaching "entry collection point"
- **Behavior**: System state switches from `idle` to `nearby`
- **Trigger Modes**:
  - Mode A (arriving): Triggers when garbage truck is N stops before entry point
  - Mode B (arrived): Triggers when garbage truck has arrived at entry point (`Arrival` field has value)

#### 2.2 Exit Collection Point Trigger
- **Condition**: Garbage truck arrives at or passes "exit collection point"
- **Behavior**: System state switches from `nearby` back to `idle`
- **Constraint**: Exit collection point must be **after** entry collection point in route order

#### 2.3 Multi-Route Processing
- Users can specify multiple route names to track
- If not specified, all routes passing through both collection points are tracked
- State triggers when garbage truck from any tracked route enters range

### FR-3: RESTful API Provision

**Description**: The system needs to provide an HTTP API for Home Assistant to poll and query current garbage truck status.

**API Specification**:
- **Endpoint**: `GET /api/trash/status`
- **Response Format**: JSON
- **Response Content**:
  - Current state (`idle`, `nearby`)
  - Trigger reason description
  - Garbage truck detailed information (route name, vehicle number, location)
  - Entry/exit collection point arrival status
  - Timestamp

### FR-4: Home Assistant Integration

**Description**: The system needs to provide complete Home Assistant configuration examples to implement automation control.

**Integration Requirements**:
- Use RESTful Sensor to regularly query system status
- Provide Binary Sensor to determine if garbage truck is nearby
- Automation rules:
  - When `binary_sensor.garbage_truck_nearby` switches to `on` → Light turns on
  - When `binary_sensor.garbage_truck_nearby` switches to `off` → Light turns off

---

## Non-Functional Requirements

### NFR-1: Performance Requirements
- API response time < 2 seconds
- Support concurrent queries from multiple users (future expansion consideration)
- System memory usage < 512 MB

### NFR-2: Reliability Requirements
- System should not crash when New Taipei City API is unavailable
- Provide error logging
- Maintain previous state when API query fails

### NFR-3: Maintainability Requirements
- Use YAML configuration file to manage all parameters
- Code must include comments
- Provide complete deployment documentation

### NFR-4: Security Requirements
- Do not log user sensitive information (coordinates only used for API queries)
- Limit API query frequency to avoid overloading New Taipei City API

---

## User Configuration Requirements

Users need to provide the following information in configuration file:

### Required Fields
1. **Home Coordinates** (lat, lng)
   - Purpose: Query New Taipei City API to get nearby garbage truck information
   - Format: Float, accurate to 6 decimal places

2. **Entry Collection Point Name** (enter_point)
   - Purpose: Collection point that triggers light on
   - Format: String, must exactly match `PointName` returned by API
   - Example: "Shuiyuan St Lane 36 Entrance"

3. **Exit Collection Point Name** (exit_point)
   - Purpose: Collection point that triggers light off
   - Format: String, must exactly match `PointName` returned by API
   - Example: "No. 28, Shuiyuan St"
   - Constraint: Must be after entry point on route

### Optional Fields
4. **Tracked Route List** (target_lines)
   - Purpose: Limit tracking to specific routes only
   - Format: String array
   - Example: ["District 3 Evening 9", "District 3 Evening 11"]
   - Default: Empty array (track all routes)

5. **Trigger Mode** (trigger_mode)
   - Purpose: Determine when to trigger entry state
   - Options:
     - `arriving`: Triggers when garbage truck is approaching entry point
     - `arrived`: Triggers when garbage truck has arrived at entry point
   - Default: `arriving`

6. **Advance Notification Stop Count** (approaching_threshold)
   - Purpose: When trigger_mode is `arriving`, how many stops in advance to trigger
   - Format: Integer
   - Example: 2 (triggers 2 stops before)
   - Default: 2

---

## System State Definition

### State Machine
System uses simple state machine to manage garbage truck status:

```
┌─────────┐
│  idle   │ ← Initial state (light off)
└────┬────┘
     │
     │ Garbage truck arrives/approaching entry collection point
     ▼
┌─────────┐
│ nearby  │ ← Garbage truck nearby (light on)
└────┬────┘
     │
     │ Garbage truck passes exit collection point
     ▼
┌─────────┐
│  idle   │ ← Return to initial state (light off)
└─────────┘
```

### State Descriptions

| State | Description | Light Status | Trigger Condition |
|-------|-------------|--------------|-------------------|
| `idle` | Garbage truck not nearby | Off 🌑 | Initial state or departed |
| `nearby` | Garbage truck nearby | On 💡 | Passed entry collection point |

---

## Constraints and Limitations

### Technical Limitations
1. Depends on New Taipei City Environmental Protection Bureau API, system cannot operate if API stops service
2. API update frequency controlled by New Taipei City government, may have delays
3. Collection point names must exactly match API data, otherwise cannot trigger

### Usage Limitations
1. Only supports garbage truck tracking within New Taipei City jurisdiction
2. Entry and exit collection points must be on the same route
3. Does not support cross-route collection point pairing

### Design Assumptions
1. Assumes users can correctly obtain their home coordinates
2. Assumes collection point names stably exist in API (will not change)
3. Assumes Home Assistant environment is correctly configured and running

---

## Future Expansion Requirements (Optional)

The following requirements are possible future expansion directions, not in first version implementation scope:

1. **Multi-user Support**: Allow multiple users to configure different collection points
2. **Push Notifications**: In addition to lights, send mobile push notifications
3. **Voice Notifications**: Integrate TTS (Text-to-Speech) voice broadcasting
4. **Historical Records**: Record garbage truck arrival times for statistical analysis
5. **Web Management Interface**: Provide graphical interface to configure collection points
6. **Map Visualization**: Display garbage truck real-time location on webpage

---

## Acceptance Criteria

### Functional Acceptance
- [ ] System can successfully query New Taipei City API and parse data
- [ ] State correctly switches to `nearby` when garbage truck passes entry collection point
- [ ] State correctly switches to `idle` when garbage truck passes exit collection point
- [ ] RESTful API can normally return JSON format data
- [ ] Home Assistant can successfully integrate and control lights

### Performance Acceptance
- [ ] API response time average < 2 seconds
- [ ] System runs continuously for 24 hours without crashes
- [ ] State switching delay < 5 minutes (limited by API query frequency)

### Reliability Acceptance
- [ ] System can properly handle errors when New Taipei City API is unavailable
- [ ] Error logs can correctly record abnormal situations
- [ ] System provides clear error messages when configuration file format is incorrect

---

## Reference Materials

- New Taipei City Garbage Truck Tracking API: `https://crd-rubbish.epd.ntpc.gov.tw/WebAPI/GetAroundPoints`
- Home Assistant Official Documentation: https://www.home-assistant.io/
- RESTful Sensor Documentation: https://www.home-assistant.io/integrations/rest/

---

**Document Version**: v1.0
**Last Updated**: 2025-11-17
**Author**: Logan
**Project Name**: trash_light
