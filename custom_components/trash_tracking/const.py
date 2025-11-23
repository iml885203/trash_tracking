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
CONF_TRIGGER_MODE = "trigger_mode"
CONF_APPROACHING_THRESHOLD = "approaching_threshold"

# Default values
DEFAULT_TRIGGER_MODE = "arriving"
DEFAULT_APPROACHING_THRESHOLD = 2
DEFAULT_SCAN_INTERVAL = 90  # seconds

# Trigger modes
TRIGGER_MODE_ARRIVING = "arriving"
TRIGGER_MODE_ARRIVED = "arrived"
