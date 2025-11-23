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
    CONF_APPROACHING_THRESHOLD,
    CONF_ENTER_POINT,
    CONF_EXIT_POINT,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_ROUTE_SELECTION,
    CONF_TRIGGER_MODE,
    DEFAULT_APPROACHING_THRESHOLD,
    DEFAULT_TRIGGER_MODE,
    DOMAIN,
    STEP_POINTS,
    STEP_ROUTE,
    STEP_USER,
    TRIGGER_MODE_ARRIVED,
    TRIGGER_MODE_ARRIVING,
)
from .trash_tracking_core.clients.ntpc_api import NTPCApiClient, NTPCApiError
from .trash_tracking_core.utils.geocoding import Geocoder, GeocodingError
from .trash_tracking_core.utils.route_analyzer import RouteAnalyzer

_LOGGER = logging.getLogger(__name__)


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
                    recommendations = await self.hass.async_add_executor_job(analyzer.analyze_routes, routes)

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
                    CONF_TRIGGER_MODE: user_input.get(CONF_TRIGGER_MODE, DEFAULT_TRIGGER_MODE),
                    CONF_APPROACHING_THRESHOLD: user_input.get(
                        CONF_APPROACHING_THRESHOLD, DEFAULT_APPROACHING_THRESHOLD
                    ),
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
                vol.Required(CONF_TRIGGER_MODE, default=DEFAULT_TRIGGER_MODE): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(
                                value=TRIGGER_MODE_ARRIVING, label="Arriving (early notification)"
                            ),
                            selector.SelectOptionDict(value=TRIGGER_MODE_ARRIVED, label="Arrived (actual arrival)"),
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_APPROACHING_THRESHOLD, default=DEFAULT_APPROACHING_THRESHOLD
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=10,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id=STEP_POINTS,
            data_schema=data_schema,
        )
