# Trash Tracking Home Assistant Integration

Native Home Assistant Integration for New Taipei City Garbage Truck Tracking.

## Installation

### HACS (Recommended)

1. Add this repository as a custom repository in HACS
2. Search for "Trash Tracking" in HACS
3. Click Install
4. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/trash_tracking` directory to your `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Trash Tracking"
4. Follow the configuration wizard:
   - Enter your address
   - Select the route you want to track
   - Configure entry and exit collection points

## Features

- **Multi-step Configuration**: Easy setup wizard
- **Auto-detection**: Automatically finds nearby routes
- **Flexible Triggers**: Choose "arriving" or "arrived" mode
- **Multiple Instances**: Track multiple routes independently

## Entities

Each configured route creates:
- `sensor.trash_tracking_[route]_status` - Current tracking status
- `binary_sensor.trash_tracking_[route]_nearby` - Binary sensor for automation
- `sensor.trash_tracking_[route]_truck_info` - Detailed truck information

## Example Automation

```yaml
automation:
  - alias: "Garbage Truck Arrived"
    trigger:
      - platform: state
        entity_id: binary_sensor.trash_tracking_route_1_nearby
        to: 'on'
    action:
      - service: light.turn_on
        target:
          entity_id: light.notification_bulb
        data:
          brightness: 255
          rgb_color: [255, 0, 0]
```

## Support

- [GitHub Issues](https://github.com/iml885203/trash_tracking/issues)
- [Documentation](https://github.com/iml885203/trash_tracking)
