"""Constants for Trash Tracking integration."""
from typing import Final

DOMAIN: Final = "trash_tracking"

# Configuration
CONF_API_URL: Final = "api_url"
DEFAULT_API_URL: Final = "http://localhost:5000"
DEFAULT_SCAN_INTERVAL: Final = 90  # seconds

# 狀態常數
STATE_IDLE: Final = "idle"
STATE_NEARBY: Final = "nearby"

# 屬性鍵
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

# 裝置資訊
MANUFACTURER: Final = "Trash Tracking"
MODEL: Final = "NTPC Garbage Truck Tracker"
