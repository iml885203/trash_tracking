"""Constants for Trash Tracking integration."""
from typing import Final

DOMAIN: Final = "trash_tracking"

# Configuration
CONF_LATITUDE: Final = "latitude"
CONF_LONGITUDE: Final = "longitude"
CONF_ENTER_POINT: Final = "enter_point"
CONF_EXIT_POINT: Final = "exit_point"
CONF_TARGET_LINES: Final = "target_lines"
CONF_TRIGGER_MODE: Final = "trigger_mode"
CONF_APPROACHING_THRESHOLD: Final = "approaching_threshold"
CONF_SCAN_INTERVAL: Final = "scan_interval"

# Defaults
DEFAULT_SCAN_INTERVAL: Final = 90  # seconds
DEFAULT_TRIGGER_MODE: Final = "arriving"
DEFAULT_APPROACHING_THRESHOLD: Final = 2

# States
STATE_IDLE: Final = "idle"
STATE_NEARBY: Final = "nearby"

# Attributes
ATTR_REASON: Final = "reason"
ATTR_TRUCK: Final = "truck"
ATTR_LINE_NAME: Final = "line_name"
ATTR_CAR_NO: Final = "car_no"
ATTR_CURRENT_RANK: Final = "current_rank"
ATTR_TOTAL_POINTS: Final = "total_points"
ATTR_ARRIVAL_DIFF: Final = "arrival_diff"
ATTR_ENTER_POINT: Final = "enter_point"
ATTR_EXIT_POINT: Final = "exit_point"
ATTR_CURRENT_LOCATION: Final = "current_location"
ATTR_AREA: Final = "area"

# Device info
MANUFACTURER: Final = "Trash Tracking"
MODEL: Final = "NTPC Garbage Truck Tracker"
