"""DataUpdateCoordinator for Trash Tracking."""
from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class TrashTrackingCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Trash Tracking data from Add-on API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_url: str,
        scan_interval: int,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            api_url: Add-on API URL (e.g., http://localhost:5000)
            scan_interval: Update interval in seconds
        """
        self.api_url = api_url.rstrip("/")
        self.session = async_get_clientsession(hass)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

        _LOGGER.debug(
            "Coordinator initialized: api_url=%s, interval=%ss",
            self.api_url,
            scan_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Add-on API.

        Returns:
            dict: Trash truck status data

        Raises:
            UpdateFailed: If fetching data fails
        """
        url = f"{self.api_url}/api/trash/status"

        try:
            _LOGGER.debug("Fetching data from: %s", url)

            async with self.session.get(url, timeout=10) as response:
                if response.status != 200:
                    error_text = await response.text()
                    _LOGGER.error(
                        "API returned status %s: %s", response.status, error_text
                    )
                    raise UpdateFailed(f"API returned status {response.status}")

                data = await response.json()
                _LOGGER.debug("Fetched data: %s", data)

                # Validate required fields
                if "status" not in data:
                    raise UpdateFailed("API response missing 'status' field")

                return data

        except TimeoutError as err:
            _LOGGER.error("Timeout fetching data from Add-on API: %s", err)
            raise UpdateFailed(f"Timeout connecting to Add-on API: {err}")

        except Exception as err:
            _LOGGER.error(
                "Unexpected error fetching data from Add-on API: %s", err, exc_info=True
            )
            raise UpdateFailed(f"Error communicating with Add-on API: {err}")
