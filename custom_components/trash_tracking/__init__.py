"""The Trash Tracking integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant

from .const import CONF_API_URL, DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import TrashTrackingCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Trash Tracking from a config entry."""
    _LOGGER.info("Setting up Trash Tracking integration (entry_id=%s)", entry.entry_id)

    api_url = entry.data[CONF_API_URL]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    _LOGGER.debug("API URL: %s, Scan Interval: %s seconds", api_url, scan_interval)

    # Create coordinator
    coordinator = TrashTrackingCoordinator(hass, api_url, scan_interval)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info("Trash Tracking integration setup complete")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Trash Tracking integration (entry_id=%s)", entry.entry_id)

    # Unload platforms
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.info("Trash Tracking integration unloaded successfully")

    return unload_ok
