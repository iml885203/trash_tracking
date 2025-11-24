"""Constants for the Trash Tracking integration."""

DOMAIN = "trash_tracking"

# Config flow steps
STEP_USER = "user"
STEP_ROUTE = "route"
STEP_POINTS = "points"

# Config keys
CONF_ADDRESS = "address"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_ROUTE_SELECTION = "route_selection"
CONF_ENTER_POINT = "enter_point"
CONF_EXIT_POINT = "exit_point"
CONF_SCHEDULE_WEEKDAYS = "schedule_weekdays"
CONF_SCHEDULE_TIME_START = "schedule_time_start"
CONF_SCHEDULE_TIME_END = "schedule_time_end"

# Default values
DEFAULT_SCAN_INTERVAL = 30  # seconds
SCHEDULE_BUFFER_MINUTES = 10  # Buffer time before/after scheduled time
