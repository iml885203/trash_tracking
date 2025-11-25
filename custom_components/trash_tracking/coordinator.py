"""DataUpdateCoordinator for Trash Tracking integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_ENTER_POINT,
    CONF_EXIT_POINT,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_ROUTE_SELECTION,
    CONF_SCHEDULE_TIME_END,
    CONF_SCHEDULE_TIME_START,
    CONF_SCHEDULE_WEEKDAYS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    SCHEDULE_BUFFER_MINUTES,
)
from .trash_tracking_core.clients.ntpc_api import NTPCApiClient, NTPCApiError
from .trash_tracking_core.core.point_matcher import PointMatcher
from .trash_tracking_core.core.state_manager import StateManager

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

        # Extract schedule information (may be None for old configs)
        self._schedule_weekdays = entry.data.get(CONF_SCHEDULE_WEEKDAYS, [])
        self._schedule_time_start = entry.data.get(CONF_SCHEDULE_TIME_START)
        self._schedule_time_end = entry.data.get(CONF_SCHEDULE_TIME_END)

        # Create point matcher
        self._point_matcher = PointMatcher(
            enter_point_name=self._enter_point_name,
            exit_point_name=self._exit_point_name,
        )

        _LOGGER.debug(
            "Coordinator initialized for route: %s (enter=%s, exit=%s)",
            self._target_line,
            self._enter_point_name,
            self._exit_point_name,
        )

    def _should_update_now(self) -> bool:
        """
        Check if we should update now based on schedule.

        Returns:
            bool: True if should update, False otherwise
        """
        # If no schedule info (old configs), always update for backward compatibility
        if not self._schedule_weekdays:
            return True

        now = datetime.now()

        # Check weekday
        # Python: 0=Monday, 6=Sunday
        # API: 0=Sunday, 1=Monday, ..., 6=Saturday
        # Convert Python weekday to API format
        python_weekday = now.weekday()  # 0-6 (Mon-Sun)
        api_weekday = python_weekday + 1 if python_weekday < 6 else 0  # Convert to API format

        if api_weekday not in self._schedule_weekdays:
            _LOGGER.debug(
                "[%s] Today (%s, weekday=%d) not in schedule %s, skipping API call",
                self._target_line,
                now.strftime("%A"),
                api_weekday,
                self._schedule_weekdays,
            )
            return False

        # Check time range (with buffer)
        if self._schedule_time_start and self._schedule_time_end:
            try:
                start_time = datetime.strptime(self._schedule_time_start, "%H:%M").time()
                end_time = datetime.strptime(self._schedule_time_end, "%H:%M").time()

                # Add buffer
                start_with_buffer = (
                    datetime.combine(now.date(), start_time) - timedelta(minutes=SCHEDULE_BUFFER_MINUTES)
                ).time()
                end_with_buffer = (
                    datetime.combine(now.date(), end_time) + timedelta(minutes=SCHEDULE_BUFFER_MINUTES)
                ).time()

                current_time = now.time()

                # Check if current time is within range
                if not (start_with_buffer <= current_time <= end_with_buffer):
                    _LOGGER.debug(
                        "[%s] Current time %s not in schedule range %s-%s (with %d min buffer), skipping API call",
                        self._target_line,
                        current_time.strftime("%H:%M"),
                        start_with_buffer.strftime("%H:%M"),
                        end_with_buffer.strftime("%H:%M"),
                        SCHEDULE_BUFFER_MINUTES,
                    )
                    return False

            except ValueError as e:
                _LOGGER.warning("Failed to parse schedule times: %s, will update anyway", e)
                return True

        # Within schedule, should update
        _LOGGER.debug("[%s] Within schedule, proceeding with API call", self._target_line)
        return True

    async def _async_update_data(self) -> dict[str, Any]:  # noqa: C901
        """Fetch data from API."""
        # Check if we should update based on schedule
        if not self._should_update_now():
            # Outside scheduled time, return idle state without API call
            if not self._state_manager.is_idle():
                self._state_manager.update_state(new_state="idle", reason="Outside scheduled operating hours")
            return self._state_manager.get_status_response()

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

            for line in target_lines:
                match_result = self._point_matcher.check_line(line, self._state_manager.current_state)

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

    @property
    def enter_point_name(self) -> str:
        """Return the enter point name."""
        return self._enter_point_name

    @property
    def exit_point_name(self) -> str:
        """Return the exit point name."""
        return self._exit_point_name

    @property
    def schedule_weekdays(self) -> list[int]:
        """Return schedule weekdays."""
        return self._schedule_weekdays

    @property
    def schedule_time_start(self) -> str | None:
        """Return schedule start time."""
        return self._schedule_time_start

    @property
    def schedule_time_end(self) -> str | None:
        """Return schedule end time."""
        return self._schedule_time_end
