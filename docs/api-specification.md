# API Specification

## Document Description

This document describes the API specifications for the Garbage Truck Dynamic Detection System, including:
1. Detailed specifications of New Taipei City Garbage Truck API (external API)
2. RESTful API specifications provided by this system to Home Assistant (internal API)

---

## 1. New Taipei City Garbage Truck API (External API)

### Basic Information

- **Name**: New Taipei City Garbage Truck Real-time Status Query API
- **Provider**: New Taipei City Environmental Protection Bureau
- **Endpoint**: `https://crd-rubbish.epd.ntpc.gov.tw/WebAPI/GetAroundPoints`
- **Method**: `POST`
- **Content-Type**: `application/x-www-form-urlencoded`

### Request Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `lat` | float | Yes | Latitude of query location | 25.005193869072745 |
| `lng` | float | Yes | Longitude of query location | 121.5099557021958 |

### Request Examples

#### cURL
```bash
curl --location 'https://crd-rubbish.epd.ntpc.gov.tw/WebAPI/GetAroundPoints' \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'lat=25.005193869072745' \
  --data-urlencode 'lng=121.5099557021958'
```

#### Python (requests)
```python
import requests

url = "https://crd-rubbish.epd.ntpc.gov.tw/WebAPI/GetAroundPoints"
payload = {
    "lat": 25.005193869072745,
    "lng": 121.5099557021958
}
headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

response = requests.post(url, data=payload, headers=headers)
data = response.json()
```

### Response Format

#### Response Structure

```json
{
  "TimeStamp": "string",      // API response timestamp (format: YYYYMMDDHHmmss)
  "LineCount": integer,        // Number of nearby routes
  "FixedCount": integer,       // Number of fixed points
  "Line": [                    // Route array
    {
      "LineID": "string",           // Route ID
      "LineName": "string",         // Route name (e.g., "District 3 Evening 9")
      "Area": "string",             // Administrative area (e.g., "Yonghe District")
      "ArrivalRank": integer,       // Current stop number on the route
      "Diff": integer,              // Time difference from schedule (minutes, positive=late, negative=early)
      "CarNO": "string",            // Garbage truck license plate
      "Location": "string",         // Current location address description
      "LocationLat": float,         // Current location latitude
      "LocationLon": float,         // Current location longitude
      "BarCode": "string",          // Barcode identification
      "Point": [                    // All stops on this route
        {
          "SourcePointID": integer,     // Source stop ID
          "Vil": "string",              // Village
          "PointName": "string",        // Stop name (e.g., "Shuiyuan St Lane 36 Entrance")
          "Lon": float,                 // Stop longitude
          "Lat": float,                 // Stop latitude
          "PointID": integer,           // Stop ID
          "PointRank": integer,         // Stop order on route (starts from 1)
          "PointTime": "string",        // Scheduled arrival time (format: HH:mm)
          "Arrival": "string",          // Actual arrival time (format: HH:mm, empty if not arrived)
          "ArrivalDiff": integer,       // Arrival time difference (minutes, 65535 means not arrived)
          "FixedPoint": integer,        // Whether it's a fixed point (0=no, 1=yes)
          "PointWeekKnd": "string",     // Weekend marker
          "InScope": "string",          // Within query range ("Y"=yes, ""=no)
          "LikeCount": integer          // Like count
        }
      ]
    }
  ]
}
```

### Response Example

```json
{
  "TimeStamp": "20251117211747",
  "LineCount": 3,
  "FixedCount": 0,
  "Line": [
    {
      "LineID": "234042",
      "LineName": "District 3 Evening 9",
      "Area": "Yonghe District",
      "ArrivalRank": 35,
      "Diff": 0,
      "CarNO": "KEJ-6632",
      "Location": "No. 28, Shuiyuan St, Yonghe District, New Taipei City",
      "LocationLat": 25.0098583333333,
      "LocationLon": 121.526181666667,
      "BarCode": "000013",
      "Point": [
        {
          "SourcePointID": 25022,
          "Vil": "Shuiyuan Village",
          "PointName": "Shuiyuan St Lane 36 Entrance",
          "Lon": 121.5109786,
          "Lat": 25.00444795,
          "PointID": 912674,
          "PointRank": 34,
          "PointTime": "19:30",
          "Arrival": "19:35",
          "ArrivalDiff": 5,
          "FixedPoint": 0,
          "PointWeekKnd": "",
          "InScope": "Y",
          "LikeCount": 0
        },
        {
          "SourcePointID": 4840,
          "Vil": "Shuiyuan Village",
          "PointName": "No. 28, Shuiyuan St",
          "Lon": 121.5114427,
          "Lat": 25.00457597,
          "PointID": 912677,
          "PointRank": 35,
          "PointTime": "19:35",
          "Arrival": "19:36",
          "ArrivalDiff": 1,
          "FixedPoint": 0,
          "PointWeekKnd": "",
          "InScope": "Y",
          "LikeCount": 0
        }
      ]
    }
  ]
}
```

### Important Field Descriptions

#### Line Object
- **ArrivalRank**: Current stop number of garbage truck (corresponds to PointRank in Point array)
- **LocationLat/LocationLon**: Real-time GPS coordinates of garbage truck

#### Point Object
- **PointRank**: Stop order, starts from 1 and increments
- **Arrival**:
  - Has value (e.g., "19:35") means arrived at this point
  - Empty string `""` means not yet arrived
- **ArrivalDiff**:
  - Positive number: Arrived later than scheduled
  - Negative number: Arrived earlier than scheduled
  - 65535: Not yet arrived
- **InScope**:
  - `"Y"`: This stop is within range of query coordinates
  - `""`: Not within range

### Error Handling

| HTTP Status Code | Description |
|------------------|-------------|
| 200 | Request successful |
| 400 | Request parameter error (missing lat or lng) |
| 500 | Internal server error |
| 503 | Service temporarily unavailable |

---

## 1.2. New Taipei City Garbage Truck API - GetArrival (Alternative Query Method)

### Basic Information

- **Name**: New Taipei City Garbage Truck Route Query API
- **Provider**: New Taipei City Environmental Protection Bureau
- **Endpoint**: `https://crd-rubbish.epd.ntpc.gov.tw/WebAPI/GetArrival`
- **Method**: `POST`
- **Content-Type**: `application/x-www-form-urlencoded`

### Differences from GetAroundPoints

| Feature | GetAroundPoints | GetArrival |
|---------|-----------------|------------|
| **Query Method** | Query nearby routes via coordinates | Direct query of specific routes via LineID |
| **Input Parameters** | lat, lng (coordinates) | LineID (comma-separated route IDs) |
| **Returned Data** | Includes route name, area, and complete information | Only includes route ID and stop information |
| **Stop Information** | Includes stop name, coordinates, village, etc. | Only includes PointID, arrival time, and basic information |
| **Use Case** | Don't know route ID, need to explore nearby routes | Already know route ID, quickly query specific route status |

### Request Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `LineID` | string | Yes | Route ID, multiple separated by commas | 234026,234042,234067 |

### Request Examples

#### cURL
```bash
curl --location 'https://crd-rubbish.epd.ntpc.gov.tw/WebAPI/GetArrival' \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data 'LineID=234026,234042,234067'
```

#### Python (requests)
```python
import requests

url = "https://crd-rubbish.epd.ntpc.gov.tw/WebAPI/GetArrival"
payload = {
    "LineID": "234026,234042,234067"
}
headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

response = requests.post(url, data=payload, headers=headers)
data = response.json()
```

### Response Format

#### Response Structure

```json
{
  "TimeStamp": "string",      // API response timestamp (format: YYYYMMDDHHmmss)
  "LineCount": integer,        // Number of routes returned
  "Line": [                    // Route array
    {
      "LineID": "string",           // Route ID
      "ArrivalRank": integer,       // Current stop number on route
      "Diff": integer,              // Time difference from schedule (minutes)
      "CarNO": "string",            // Garbage truck license plate
      "Location": "string",         // Current location address description
      "LocationLat": float,         // Current location latitude
      "LocationLon": float,         // Current location longitude
      "BarCode": "string",          // Barcode identification
      "Point": [                    // All stops on this route
        {
          "PointID": integer,           // Stop ID
          "PointRank": integer,         // Stop order on route (starts from 1)
          "PointTime": "string",        // Scheduled arrival time (format: HH:mm)
          "Arrival": "string",          // Actual arrival time (format: HH:mm, empty if not arrived)
          "ArrivalDiff": integer        // Arrival time difference (minutes)
        }
      ]
    }
  ]
}
```

**Note**: Point data from this API does not include stop name, coordinates, village, and other detailed information, only ID and time information.

### Response Example

```json
{
  "TimeStamp": "20251117213304",
  "LineCount": 1,
  "Line": [
    {
      "LineID": "234026",
      "ArrivalRank": 36,
      "Diff": 8,
      "CarNO": "BWM-8152",
      "Location": "No. 1, Fude Rd, Yonghe District, New Taipei City",
      "LocationLat": 25.00998,
      "LocationLon": 121.526588333333,
      "BarCode": "000004",
      "Point": [
        {
          "PointID": 904739,
          "PointRank": 1,
          "PointTime": "17:40",
          "Arrival": "17:39",
          "ArrivalDiff": -1
        },
        {
          "PointID": 904742,
          "PointRank": 2,
          "PointTime": "17:44",
          "Arrival": "17:42",
          "ArrivalDiff": -2
        }
      ]
    }
  ]
}
```

### Pros and Cons Analysis

#### Advantages
1. **More lightweight**: Less data returned, faster network transmission
2. **More precise**: Direct query of specified routes, no filtering needed
3. **Better performance**: Lower server load, possibly faster response

#### Disadvantages
1. **Need to know LineID in advance**: Must first obtain route ID via GetAroundPoints
2. **Lack of detailed stop information**: Cannot get stop names, need to maintain PointID mapping separately
3. **Cannot discover new routes**: If routes change or are added, cannot auto-detect

### Usage Recommendations

#### Recommend Using GetAroundPoints (Currently Adopted)
- Suitable when route ID is uncertain
- Can match based on stop names (e.g., "Shuiyuan St Lane 36 Entrance")
- No need to modify configuration when routes change

#### Consider Using GetArrival When
- Route IDs are fixed and won't change
- Need to track multiple specific routes
- Have strict requirements for network traffic or response speed
- Willing to maintain PointID to stop name mapping

### Integration Example

If deciding to use GetArrival API, modifications needed:

```python
# Store LineID and PointID in config instead
tracking:
  target_line_ids:
    - "234042"  # District 3 Evening 9
  enter_point_id: 912674  # PointID for Shuiyuan St Lane 36 Entrance
  exit_point_id: 912677   # PointID for No. 28, Shuiyuan St

# API client modification
def get_line_status(self, line_ids: List[str]) -> dict:
    url = f"{self.BASE_URL}/GetArrival"
    payload = {"LineID": ",".join(line_ids)}
    response = self.session.post(url, data=payload, headers=self.headers)
    return response.json()
```

---

## 2. System Internal API (For Home Assistant)

### Basic Information

- **Name**: Garbage Truck Status Query API
- **Endpoint**: `http://localhost:5000/api/trash/status`
- **Method**: `GET`
- **Content-Type**: `application/json`

### Request Parameters

No parameters needed, direct GET request.

### Request Examples

#### cURL
```bash
curl http://localhost:5000/api/trash/status
```

#### Python (requests)
```python
import requests

response = requests.get("http://localhost:5000/api/trash/status")
data = response.json()
```

### Response Format

#### Status: idle (No garbage truck nearby)

```json
{
  "status": "idle",
  "reason": "No garbage truck nearby",
  "truck": null,
  "timestamp": "2025-11-17T21:00:00+08:00"
}
```

#### Status: nearby (Garbage truck nearby)

```json
{
  "status": "nearby",
  "reason": "Garbage truck approaching entry collection point",
  "truck": {
    "line_name": "District 3 Evening 9",
    "line_id": "234042",
    "car_no": "KEJ-6632",
    "area": "Yonghe District",
    "current_location": "Shuiyuan St Lane 14 Entrance, Yonghe District, New Taipei City",
    "current_lat": 25.0098583,
    "current_lon": 121.5261817,
    "current_rank": 32,
    "total_points": 71,
    "arrival_diff": 0,
    "enter_point": {
      "name": "Shuiyuan St Lane 36 Entrance",
      "rank": 34,
      "point_time": "19:30",
      "arrival": "",
      "arrival_diff": 65535,
      "passed": false,
      "distance_to_current": 2
    },
    "exit_point": {
      "name": "No. 28, Shuiyuan St",
      "rank": 35,
      "point_time": "19:35",
      "arrival": "",
      "arrival_diff": 65535,
      "passed": false,
      "distance_to_current": 3
    }
  },
  "timestamp": "2025-11-17T21:00:00+08:00"
}
```

### Response Field Descriptions

#### Root Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | System status: `idle` or `nearby` |
| `reason` | string | Text description of status reason |
| `truck` | object \| null | Garbage truck detailed information, null when no truck |
| `timestamp` | string | API response time (ISO 8601 format) |

#### truck Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `line_name` | string | Route name |
| `line_id` | string | Route ID |
| `car_no` | string | License plate number |
| `area` | string | Administrative area |
| `current_location` | string | Current location description |
| `current_lat` | float | Current latitude |
| `current_lon` | float | Current longitude |
| `current_rank` | integer | Current stop number |
| `total_points` | integer | Total stops on route |
| `arrival_diff` | integer | Time difference from schedule (minutes) |
| `enter_point` | object | Entry collection point detailed information |
| `exit_point` | object | Exit collection point detailed information |

#### enter_point / exit_point Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Collection point name |
| `rank` | integer | Point order on route |
| `point_time` | string | Scheduled arrival time (HH:mm) |
| `arrival` | string | Actual arrival time (HH:mm), empty if not arrived |
| `arrival_diff` | integer | Arrival time difference (65535 means not arrived) |
| `passed` | boolean | Whether truck has passed this point |
| `distance_to_current` | integer | Number of stops from truck's current location |

### HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Request successful |
| 500 | Internal server error |
| 503 | Unable to connect to New Taipei City API |

### Error Response Format

```json
{
  "error": "Error message",
  "detail": "Detailed error description",
  "timestamp": "2025-11-17T21:00:00+08:00"
}
```

---

## 3. Integration Example: Home Assistant Configuration

### configuration.yaml

```yaml
# RESTful Sensor - Query garbage truck status
sensor:
  - platform: rest
    name: "Garbage Truck Monitor"
    resource: "http://localhost:5000/api/trash/status"
    scan_interval: 90  # Query every 90 seconds
    json_attributes:
      - reason
      - truck
      - timestamp
    value_template: "{{ value_json.status }}"

# Binary Sensor - Determine if garbage truck is nearby
binary_sensor:
  - platform: template
    sensors:
      garbage_truck_nearby:
        friendly_name: "Garbage Truck Nearby"
        value_template: "{{ is_state('sensor.garbage_truck_monitor', 'nearby') }}"
        device_class: presence
        attribute_templates:
          line_name: "{{ state_attr('sensor.garbage_truck_monitor', 'truck')['line_name'] if state_attr('sensor.garbage_truck_monitor', 'truck') else 'N/A' }}"
          car_no: "{{ state_attr('sensor.garbage_truck_monitor', 'truck')['car_no'] if state_attr('sensor.garbage_truck_monitor', 'truck') else 'N/A' }}"
          current_location: "{{ state_attr('sensor.garbage_truck_monitor', 'truck')['current_location'] if state_attr('sensor.garbage_truck_monitor', 'truck') else 'N/A' }}"
```

### Automation Examples

```yaml
# Automation: Garbage truck arrival - Turn on light
automation:
  - alias: "Garbage Truck Arrival - Turn On Notification Light"
    description: "Turn on light when garbage truck enters designated collection point range"
    trigger:
      - platform: state
        entity_id: binary_sensor.garbage_truck_nearby
        to: 'on'
    action:
      - service: light.turn_on
        target:
          entity_id: light.notification_bulb
        data:
          brightness: 255
          color_name: "red"
      - service: notify.mobile_app
        data:
          title: "🚛 Garbage Truck is Here!"
          message: "{{ state_attr('sensor.garbage_truck_monitor', 'reason') }}"

  - alias: "Garbage Truck Departure - Turn Off Notification Light"
    description: "Turn off light when garbage truck leaves designated collection point range"
    trigger:
      - platform: state
        entity_id: binary_sensor.garbage_truck_nearby
        to: 'off'
    action:
      - service: light.turn_off
        target:
          entity_id: light.notification_bulb
```

---

## 4. API Testing Guide

### Test New Taipei City API - GetAroundPoints

```bash
# Test query for nearby garbage trucks in Yonghe District
curl --location 'https://crd-rubbish.epd.ntpc.gov.tw/WebAPI/GetAroundPoints' \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'lat=25.005193869072745' \
  --data-urlencode 'lng=121.5099557021958' | jq
```

### Test New Taipei City API - GetArrival

```bash
# Test query for specific routes (using LineID obtained from GetAroundPoints)
curl --location 'https://crd-rubbish.epd.ntpc.gov.tw/WebAPI/GetArrival' \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data 'LineID=234026,234042,234067' | jq

# Compare data differences between the two APIs
# Note: GetArrival's Point object does not include PointName, Lat, Lon fields
```

### Test System Internal API

```bash
# Test after starting Flask service
curl http://localhost:5000/api/trash/status | jq

# Test error handling (when service is not started)
curl http://localhost:5000/api/trash/status
```

### Python Test Script

```python
import requests
import json

def test_system_api():
    """Test system internal API"""
    url = "http://localhost:5000/api/trash/status"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))

        # Verify required fields
        assert "status" in data
        assert "timestamp" in data
        assert data["status"] in ["idle", "nearby"]

        if data["status"] == "nearby":
            assert "truck" in data
            assert data["truck"] is not None

        print("✅ API test passed")

    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
    except AssertionError as e:
        print(f"❌ Data format validation failed: {e}")

if __name__ == "__main__":
    test_system_api()
```

---

## 5. API Limitations and Notes

### New Taipei City API Limitations
1. **Query Frequency**: Recommended not to exceed once per minute to avoid server overload
2. **Response Size**: May return large amounts of route data, recommend using gzip compression
3. **Real-time Nature**: Garbage truck location updates may have 1-2 minute delay
4. **Availability**: No SLA guarantee, may be suspended for maintenance

### System Internal API Limitations
1. **Single-threaded**: Currently designed for single user use
2. **No Authentication**: API authentication mechanism not implemented
3. **State Storage**: Only stores state in memory, lost after restart

---

**Document Version**: v1.0
**Last Updated**: 2025-11-17
**Maintainer**: Logan
