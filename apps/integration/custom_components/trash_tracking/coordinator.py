"""DataUpdateCoordinator for Trash Tracking integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from trash_tracking_core import NTPCApiClient, NTPCApiError, PointMatcher, StateManager

from .const import (
    CONF_APPROACHING_THRESHOLD,
    CONF_ENTER_POINT,
    CONF_EXIT_POINT,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_ROUTE_SELECTION,
    CONF_TRIGGER_MODE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class TrashTrackingCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Trash Tracking data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

        self.entry = entry
        self._api_client = NTPCApiClient()
        self._state_manager = StateManager()

        # Extract config from entry
        self._latitude = entry.data[CONF_LATITUDE]
        self._longitude = entry.data[CONF_LONGITUDE]
        self._target_line = entry.data[CONF_ROUTE_SELECTION]
        self._enter_point_name = entry.data[CONF_ENTER_POINT]
        self._exit_point_name = entry.data[CONF_EXIT_POINT]
        self._trigger_mode = entry.data[CONF_TRIGGER_MODE]
        self._approaching_threshold = entry.data[CONF_APPROACHING_THRESHOLD]

        # Create point matcher
        self._point_matcher = PointMatcher(
            enter_point_name=self._enter_point_name,
            exit_point_name=self._exit_point_name,
            trigger_mode=self._trigger_mode,
            approaching_threshold=self._approaching_threshold,
        )

        _LOGGER.debug(
            "Coordinator initialized for route: %s (enter=%s, exit=%s)",
            self._target_line,
            self._enter_point_name,
            self._exit_point_name,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            # Fetch truck data from API (blocking I/O, run in executor)
            truck_lines = await self.hass.async_add_executor_job(
                self._api_client.get_around_points,
                self._latitude,
                self._longitude,
                0,  # time_filter: 0 = no filter
            )

            if not truck_lines:
                _LOGGER.debug("No truck data returned from API")
                if not self._state_manager.is_idle():
                    self._state_manager.update_state(new_state="idle", reason="No trucks nearby")
                return self._state_manager.get_status_response()

            # Filter for target route
            target_lines = [line for line in truck_lines if line.line_name == self._target_line]

            if not target_lines:
                _LOGGER.debug("Target route %s not found in nearby trucks", self._target_line)
                if not self._state_manager.is_idle():
                    self._state_manager.update_state(new_state="idle", reason="Tracked route not nearby")
                return self._state_manager.get_status_response()

            # Check if route matches entry/exit points
            for line in target_lines:
                match_result = self._point_matcher.check_line(line)

                if match_result.should_trigger:
                    self._state_manager.update_state(
                        new_state=match_result.new_state,
                        reason=match_result.reason,
                        truck_line=match_result.truck_line,
                        enter_point=match_result.enter_point,
                        exit_point=match_result.exit_point,
                    )
                    break
            else:
                _LOGGER.debug("No route triggered state change")

            return self._state_manager.get_status_response()

        except NTPCApiError as err:
            _LOGGER.error("Error communicating with API: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        except Exception as err:
            _LOGGER.exception("Unexpected error fetching data: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err

    @property
    def route_name(self) -> str:
        """Return the route name."""
        return self._target_line

    @property
    def is_nearby(self) -> bool:
        """Return True if truck is nearby."""
        return self.data and self.data.get("status") == "nearby"

    @property
    def status(self) -> str:
        """Return the current status."""
        return self.data.get("status", "unknown") if self.data else "unknown"

    @property
    def reason(self) -> str:
        """Return the status reason."""
        return self.data.get("reason", "") if self.data else ""

    @property
    def truck_info(self) -> dict[str, Any] | None:
        """Return truck information if available."""
        return self.data.get("truck") if self.data else None
