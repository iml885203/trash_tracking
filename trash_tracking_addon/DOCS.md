# Trash Tracking - Complete Documentation

## Quick Start

### 1. Install Add-on

1. In Home Assistant, go to **Supervisor** → **Add-on Store**
2. Three dots (top right) → **Repositories**
3. Add: `https://github.com/iml885203/trash_tracking`
4. Find "Trash Tracking" and install

### 2. Configure Add-on

Click the **Configuration** tab:

```yaml
location:
  lat: 25.018269          # Change to your latitude
  lng: 121.471703         # Change to your longitude
tracking:
  target_lines: []        # Leave empty to track all routes, or specify routes
  enter_point: "Minsheng Rd. Sec. 2, No. 80"    # Change to your entry point
  exit_point: "Chenggong Rd. No. 23"             # Change to your exit point
  trigger_mode: "arriving"
  approaching_threshold: 2
```

### 3. Start Add-on

Click the **Start** button

### 4. Configure Home Assistant

Edit `configuration.yaml`:

```yaml
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

binary_sensor:
  - platform: template
    sensors:
      garbage_truck_nearby:
        friendly_name: "Garbage Truck Nearby"
        value_template: "{{ is_state('sensor.garbage_truck_monitor', 'nearby') }}"
        device_class: presence

automation:
  - alias: "Turn on light when truck arrives"
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
```

Reload configuration: **Developer Tools** → **YAML** → **Reload All YAML**

## How to Find Collection Point Names

### Method 1: Using Add-on Built-in CLI

1. Go to **Supervisor** → **System** → **Terminal**
2. Execute:
```bash
docker exec -it $(docker ps | grep trash_tracking | awk '{print $1}') \
  python3 cli.py --lat YOUR_LATITUDE --lng YOUR_LONGITUDE
```

Example output:
```
✅ Found 3 garbage trucks

🚛 Route: C08 Afternoon Route
   Vehicle: KES-6950

📍 Next 10 collection points:
   1. [⏳ Scheduled 14:00] Minsheng Rd. Sec. 2, No. 80    ← Use as entry point
   2. [⏳ Scheduled 14:05] Minsheng Rd. Sec. 2, No. 100
   3. [⏳ Scheduled 14:10] Chenggong Rd. No. 23           ← Use as exit point
```

### Method 2: Using New Taipei City Official Website

Visit: https://crd-rubbish.epd.ntpc.gov.tw/

## Configuration Options

### location (Required)

Your home GPS coordinates

- `lat`: Latitude (float)
- `lng`: Longitude (float)

**How to get coordinates**:
- Google Maps: Right-click on map → Display coordinates
- Or use mobile GPS app

### tracking (Required)

Tracking configuration

- `target_lines`: List of route names to track
  - Empty `[]` = Track all passing routes
  - Specify routes = Only track specific routes
  - Example: `["C08 Afternoon Route", "C15 Afternoon Route"]`

- `enter_point`: Entry collection point name (string)
  - Status changes to `nearby` when truck reaches this point
  - Must match API response exactly

- `exit_point`: Exit collection point name (string)
  - Status changes to `idle` when truck passes this point
  - Must be after enter_point in route order

- `trigger_mode`: Trigger mode
  - `arriving`: Trigger before arrival (Recommended)
  - `arrived`: Trigger on arrival

- `approaching_threshold`: Number of stops ahead to notify (0-10)
  - Only effective when `trigger_mode: arriving`
  - Example: Set to 2 = Notify 2 stops in advance
  - Set to 0 = Notify on arrival

### system (Optional)

System configuration

- `log_level`: Log level
  - `DEBUG`: Detailed debug messages
  - `INFO`: General information (default)
  - `WARNING`: Warning messages
  - `ERROR`: Error messages only

### api (Optional)

API configuration

- `ntpc.timeout`: API request timeout (seconds, 5-30)
- `ntpc.retry_count`: Number of retries (1-10)
- `ntpc.retry_delay`: Retry delay (seconds, 1-10)

## Usage Examples

### Example 1: Basic Configuration (Single Route)

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

### Example 2: Track All Routes

```yaml
location:
  lat: 25.018269
  lng: 121.471703
tracking:
  target_lines: []  # Empty
  enter_point: "Minsheng Rd. Sec. 2, No. 80"
  exit_point: "Chenggong Rd. No. 23"
  trigger_mode: "arriving"
  approaching_threshold: 3  # 3 stops ahead
```

### Example 3: Multiple Route Tracking

```yaml
location:
  lat: 25.018269
  lng: 121.471703
tracking:
  target_lines:
    - "C08 Afternoon Route"
    - "C15 Afternoon Route"
    - "C17 Afternoon Route"
  enter_point: "Minsheng Rd. Sec. 2, No. 80"
  exit_point: "Chenggong Rd. No. 23"
  trigger_mode: "arriving"
  approaching_threshold: 2
```

### Example 4: Actual Arrival Mode

```yaml
location:
  lat: 25.018269
  lng: 121.471703
tracking:
  target_lines: []
  enter_point: "Minsheng Rd. Sec. 2, No. 80"
  exit_point: "Chenggong Rd. No. 23"
  trigger_mode: "arrived"  # Notify on actual arrival
  approaching_threshold: 0  # This parameter has no effect
```

## Home Assistant Integration Examples

### Complete Automation Examples

```yaml
automation:
  # 1. Turn on notification light when truck arrives
  - alias: "Garbage Truck Arrival - Turn On Light"
    trigger:
      - platform: state
        entity_id: binary_sensor.garbage_truck_nearby
        to: 'on'
    action:
      # Turn on red light
      - service: light.turn_on
        target:
          entity_id: light.notification_bulb
        data:
          brightness: 255
          rgb_color: [255, 0, 0]
      # Send mobile notification
      - service: notify.mobile_app_iphone
        data:
          title: "🚛 Garbage Truck Arriving!"
          message: "Garbage truck approaching, please prepare trash"
          data:
            push:
              sound: "US-EN-Morgan-Freeman-Garbage-Truck.wav"

  # 2. Turn off notification light when truck leaves
  - alias: "Garbage Truck Departure - Turn Off Light"
    trigger:
      - platform: state
        entity_id: binary_sensor.garbage_truck_nearby
        to: 'off'
    action:
      - service: light.turn_off
        target:
          entity_id: light.notification_bulb
      - service: notify.mobile_app_iphone
        data:
          title: "✅ Garbage Truck Departed"
          message: "Notification light turned off"

  # 3. Notify only during evening hours
  - alias: "Garbage Truck Arrival - Evening Only"
    trigger:
      - platform: state
        entity_id: binary_sensor.garbage_truck_nearby
        to: 'on'
    condition:
      - condition: time
        after: "18:00:00"
        before: "22:00:00"
    action:
      - service: light.turn_on
        target:
          entity_id: light.notification_bulb
        data:
          brightness: 255
          rgb_color: [255, 0, 0]
```

### Lovelace Card Example

```yaml
type: entities
title: Trash Tracking
entities:
  - entity: binary_sensor.garbage_truck_nearby
    name: Truck Status
  - entity: sensor.garbage_truck_monitor
    name: Details
    type: attribute
    attribute: reason
```

## Troubleshooting

### Issue 1: Add-on Won't Start

**Steps to Check**:

1. View logs:
```
Supervisor → Add-ons → Trash Tracking → Log
```

2. Common errors:
```
Error: Invalid configuration
```
→ Check YAML formatting, ensure proper indentation

```
Error: Port 5000 already in use
```
→ Another service is using port 5000, stop that service

### Issue 2: Sensor Always Shows Unavailable

**Solution**:

1. Confirm Add-on is running:
```bash
# In Terminal add-on
docker ps | grep trash_tracking
```

2. Test API:
```bash
curl http://localhost:5000/health
```

3. Check if URL in configuration.yaml is correct

### Issue 3: Status Always Shows Idle

**Possible Causes**:

1. Incorrect coordinates
2. Incorrect collection point names
3. Truck hasn't arrived yet

**Check Method**:

```bash
# Check if trucks are nearby
docker exec -it $(docker ps | grep trash_tracking | awk '{print $1}') \
  python3 cli.py --lat YOUR_LATITUDE --lng YOUR_LONGITUDE --debug
```

### Issue 4: Uncertain About Collection Point Names

**Solution**:

Enable DEBUG mode to see detailed information:

```yaml
system:
  log_level: "DEBUG"
```

Then check Add-on logs to see all found collection points.

## API Reference

### GET `/api/trash/status`

Get garbage truck status

**Response fields**:
- `status`: `idle` or `nearby`
- `reason`: Status reason description
- `truck`: Truck information (only when nearby)
- `timestamp`: Timestamp

### GET `/health`

Health check

**Response**:
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

### POST `/api/reset`

Reset tracker (for testing)

## Advanced Tips

### Using Conditions to Avoid False Triggers

```yaml
automation:
  - alias: "Garbage Truck Arrival - Smart Notification"
    trigger:
      - platform: state
        entity_id: binary_sensor.garbage_truck_nearby
        to: 'on'
    condition:
      # Only notify when at home
      - condition: state
        entity_id: person.logan
        state: 'home'
      # Only during dinner time
      - condition: time
        after: "18:00:00"
        before: "21:00:00"
    action:
      - service: light.turn_on
        target:
          entity_id: light.notification_bulb
```

### Voice Announcement

```yaml
action:
  - service: tts.google_translate_say
    entity_id: media_player.google_home
    data:
      message: "Garbage truck arriving, please prepare trash"
```

## Support

- GitHub: https://github.com/iml885203/trash_tracking
- Issues: https://github.com/iml885203/trash_tracking/issues
