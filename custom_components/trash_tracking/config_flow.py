"""Config flow for Trash Tracking integration."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_API_URL,
    DEFAULT_API_URL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def validate_api_connection(hass: HomeAssistant, api_url: str) -> dict[str, Any]:
    """Validate that we can connect to the Add-on API.

    Args:
        hass: Home Assistant instance
        api_url: Add-on API URL

    Returns:
        dict: Info from /health endpoint

    Raises:
        ValueError: If connection fails
    """
    session = async_get_clientsession(hass)
    api_url = api_url.rstrip("/")

    try:
        # Test /health endpoint
        async with session.get(f"{api_url}/health", timeout=10) as response:
            if response.status != 200:
                raise ValueError(f"API returned status {response.status}")

            data = await response.json()
            _LOGGER.debug("Health check response: %s", data)

            if data.get("status") != "ok":
                raise ValueError("API health check failed")

            return {
                "title": "Trash Tracking",
                "config": data.get("config", {}),
            }

    except Exception as err:
        _LOGGER.error("Error connecting to Add-on API: %s", err)
        raise ValueError(f"Cannot connect to Add-on API: {err}")


class TrashTrackingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Trash Tracking."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - API connection setup.

        This is the simple mode where user just provides API URL.
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate API connection
                info = await validate_api_connection(
                    self.hass, user_input[CONF_API_URL]
                )

                # Set unique ID to prevent duplicate entries
                await self.async_set_unique_id(user_input[CONF_API_URL])
                self._abort_if_unique_id_configured()

                _LOGGER.info(
                    "Successfully validated API connection: %s", user_input[CONF_API_URL]
                )

                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                )

            except ValueError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # Show form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_URL, default=DEFAULT_API_URL): cv.string,
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=DEFAULT_SCAN_INTERVAL,
                    ): cv.positive_int,
                }
            ),
            errors=errors,
            description_placeholders={
                "default_url": DEFAULT_API_URL,
                "info": "請輸入垃圾車追蹤 Add-on 的 API 位址。如果 Add-on 安裝在同一台機器，使用預設值即可。",
            },
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return TrashTrackingOptionsFlowHandler(config_entry)


class TrashTrackingOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Trash Tracking."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.data.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): cv.positive_int,
                }
            ),
        )
