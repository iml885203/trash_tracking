"""Binary sensor platform for Trash Tracking integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TrashTrackingCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Trash Tracking binary sensors."""
    coordinator: TrashTrackingCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([TrashTrackingBinarySensor(coordinator, entry)])


class TrashTrackingBinarySensor(CoordinatorEntity[TrashTrackingCoordinator], BinarySensorEntity):
    """Representation of a Trash Tracking binary sensor."""

    _attr_device_class = BinarySensorDeviceClass.PRESENCE
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TrashTrackingCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._entry = entry

        # Generate unique ID
        self._attr_unique_id = f"{entry.entry_id}_nearby"
        self._attr_name = "Nearby"

    @property
    def is_on(self) -> bool:
        """Return True if truck is nearby."""
        return self.coordinator.is_nearby

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            "status": self.coordinator.status,
            "reason": self.coordinator.reason,
            "route_name": self.coordinator.route_name,
        }

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": f"Trash Tracking {self.coordinator.route_name}",
            "manufacturer": "Logan",
            "model": "Garbage Truck Tracker",
            "sw_version": "2025.11.6",
        }
