"""The Trash Tracking integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import TrashTrackingCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.DEVICE_TRACKER]


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry to new version."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        new_data = {**config_entry.data}
        new_data.setdefault("nearest_point", None)
        new_data.setdefault("nearest_point_rank", None)
        new_data.setdefault("enter_point_rank", None)
        new_data.setdefault("exit_point_rank", None)
        hass.config_entries.async_update_entry(config_entry, data=new_data, version=2)

    _LOGGER.info("Migration to version %s successful", config_entry.version)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Trash Tracking from a config entry."""
    _LOGGER.debug("Setting up Trash Tracking integration")

    # Create coordinator
    coordinator = TrashTrackingCoordinator(hass, entry)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Trash Tracking integration")

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Remove coordinator
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
