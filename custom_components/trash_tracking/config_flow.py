"""Config flow for Trash Tracking integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_ADDRESS,
    CONF_ENTER_POINT,
    CONF_EXIT_POINT,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_ROUTE_SELECTION,
    CONF_SCHEDULE_TIME_END,
    CONF_SCHEDULE_TIME_START,
    CONF_SCHEDULE_WEEKDAYS,
    DOMAIN,
    STEP_POINTS,
    STEP_ROUTE,
    STEP_USER,
)
from .trash_tracking_core.clients.ntpc_api import NTPCApiClient, NTPCApiError
from .trash_tracking_core.utils.geocoding import Geocoder, GeocodingError
from .trash_tracking_core.utils.route_analyzer import RouteAnalyzer

_LOGGER = logging.getLogger(__name__)


def _extract_schedule_from_route(
    route_recommendation: Any, api_client: Any, latitude: float, longitude: float
) -> dict[str, Any]:
    """
    Extract schedule information from route recommendation.

    Since PointWeekKnd only indicates waste types (N=Normal, R=Recyclable, F=Food),
    we need to query the API with different week parameters to determine collection days.

    Args:
        route_recommendation: Route recommendation object
        api_client: NTPCApiClient instance for querying API
        latitude: User's latitude
        longitude: User's longitude

    Returns:
        dict: Schedule information with keys:
            - weekdays: list[int] - List of weekday numbers (0=Sunday, 1-6=Monday-Saturday)
            - time_start: str - Earliest collection time (HH:MM format)
            - time_end: str - Latest collection time (HH:MM format)
    """
    points = route_recommendation.truck.points
    route_name = route_recommendation.truck.line_name

    # Determine collection weekdays by querying API with each week value
    # week: 0=Sunday, 1=Monday, ..., 6=Saturday
    collection_weekdays = []

    _LOGGER.debug("Determining collection days for route: %s", route_name)

    for week in range(7):
        try:
            trucks = api_client.get_around_points(lat=latitude, lng=longitude, week=week)

            # Check if this route appears in the results
            route_found = any(truck.line_name == route_name for truck in trucks)

            if route_found:
                collection_weekdays.append(week)
                _LOGGER.debug("Route %s collects on week=%d", route_name, week)

        except Exception as e:
            _LOGGER.warning("Failed to query API for week=%d: %s", week, e)
            # Continue checking other days even if one fails

    # Find earliest and latest collection times
    times = [point.point_time for point in points if point.point_time]

    schedule = {
        "weekdays": collection_weekdays,
        "time_start": min(times) if times else None,
        "time_end": max(times) if times else None,
    }

    _LOGGER.debug(
        "Extracted schedule: weekdays=%s, time_start=%s, time_end=%s",
        schedule["weekdays"],
        schedule["time_start"],
        schedule["time_end"],
    )

    return schedule


class TrashTrackingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Trash Tracking."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._address: str | None = None
        self._latitude: float | None = None
        self._longitude: float | None = None
        self._route_recommendations: list[Any] | None = None
        self._selected_route: Any | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step - address input."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS]

            try:
                # Step 1: Geocode address
                geocoder = Geocoder()
                lat, lng = await self.hass.async_add_executor_job(geocoder.address_to_coordinates, address)

                # Step 2: Find nearby routes (use week=1 for Monday)
                api_client = NTPCApiClient()
                routes = await self.hass.async_add_executor_job(api_client.get_around_points, lat, lng, 0, 1)

                if not routes:
                    errors["base"] = "no_routes_found"
                else:
                    # Step 3: Analyze routes and generate recommendations
                    analyzer = RouteAnalyzer(lat, lng)
                    recommendations = await self.hass.async_add_executor_job(analyzer.analyze_all_routes, routes)

                    if not recommendations:
                        errors["base"] = "no_routes_found"
                    else:
                        # Store results
                        self._address = address
                        self._latitude = lat
                        self._longitude = lng
                        self._route_recommendations = recommendations

                        _LOGGER.debug(
                            f"Found {len(self._route_recommendations)} route recommendations for address: {address}"
                        )

                    # Move to route selection step
                    return await self.async_step_route()

            except GeocodingError:
                errors["base"] = "invalid_address"
            except NTPCApiError:
                errors["base"] = "cannot_connect"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception: %s", err)
                errors["base"] = "unknown"

        # Show form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_ADDRESS): str,
            }
        )

        return self.async_show_form(
            step_id=STEP_USER,
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_route(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the route selection step."""
        if user_input is not None:
            # Find selected route
            selected_route_name = user_input[CONF_ROUTE_SELECTION]
            self._selected_route = next(
                (r for r in self._route_recommendations if r.truck.line_name == selected_route_name), None
            )

            if self._selected_route:
                # Move to points configuration step
                return await self.async_step_points()

        # Build route options (route name as both key and label)
        route_options = {route.truck.line_name: route.truck.line_name for route in self._route_recommendations}

        data_schema = vol.Schema(
            {
                vol.Required(CONF_ROUTE_SELECTION): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[selector.SelectOptionDict(value=k, label=v) for k, v in route_options.items()],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id=STEP_ROUTE,
            data_schema=data_schema,
        )

    async def async_step_points(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the collection points configuration step."""
        if user_input is not None:
            # Extract schedule information from selected route
            # This requires querying API 7 times (once for each day of week)
            from .trash_tracking_core.clients.ntpc_api import NTPCApiClient

            api_client = NTPCApiClient()
            schedule = await self.hass.async_add_executor_job(
                _extract_schedule_from_route,
                self._selected_route,
                api_client,
                self._latitude,
                self._longitude,
            )

            # Create entry
            title = f"{self._selected_route.truck.line_name}"

            return self.async_create_entry(
                title=title,
                data={
                    CONF_ADDRESS: self._address,
                    CONF_LATITUDE: self._latitude,
                    CONF_LONGITUDE: self._longitude,
                    CONF_ROUTE_SELECTION: self._selected_route.truck.line_name,
                    CONF_ENTER_POINT: user_input[CONF_ENTER_POINT],
                    CONF_EXIT_POINT: user_input[CONF_EXIT_POINT],
                    CONF_SCHEDULE_WEEKDAYS: schedule["weekdays"],
                    CONF_SCHEDULE_TIME_START: schedule["time_start"],
                    CONF_SCHEDULE_TIME_END: schedule["time_end"],
                },
            )

        # Build collection point options from selected route
        point_options = {
            point.point_name: f"{point.point_name} (#{point.point_rank}, {point.point_time})"
            for point in self._selected_route.truck.points
        }

        # Default values from recommendation
        default_enter = self._selected_route.enter_point.point_name
        default_exit = self._selected_route.exit_point.point_name

        data_schema = vol.Schema(
            {
                vol.Required(CONF_ENTER_POINT, default=default_enter): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[selector.SelectOptionDict(value=k, label=v) for k, v in point_options.items()],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(CONF_EXIT_POINT, default=default_exit): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[selector.SelectOptionDict(value=k, label=v) for k, v in point_options.items()],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id=STEP_POINTS,
            data_schema=data_schema,
        )
