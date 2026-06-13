"""Device tracker platform for Trash Tracking integration.

Exposes each tracked route's garbage truck as a GPS ``device_tracker`` so its
live position shows up on the Home Assistant map. The dot only appears while
the truck has a live position this update cycle; idle / out-of-schedule cycles
make the entity unavailable so no stale dots linger when multiple routes are
configured.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TrashTrackingCoordinator
from .trash_tracking_core.core.location import TruckLocation, resolve_truck_location

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Trash Tracking device tracker."""
    coordinator: TrashTrackingCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([TrashTrackingDeviceTracker(coordinator, entry)])


class TrashTrackingDeviceTracker(CoordinatorEntity[TrashTrackingCoordinator], TrackerEntity):
    """Representation of a tracked truck's live GPS position."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:truck"

    def __init__(
        self,
        coordinator: TrashTrackingCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the device tracker."""
        super().__init__(coordinator)
        self._entry = entry

        # Generate unique ID
        self._attr_unique_id = f"{entry.entry_id}_location"
        self._attr_name = "Location"

    @property
    def _location(self) -> TruckLocation:
        """Resolve the current map position from coordinator data."""
        return resolve_truck_location(self.coordinator.data)

    @property
    def source_type(self) -> SourceType:
        """Return the source type of the device."""
        return SourceType.GPS

    @property
    def available(self) -> bool:
        """Return True only while the truck has a live position to show."""
        return super().available and self._location.available

    @property
    def latitude(self) -> float | None:
        """Return the truck's latitude."""
        return self._location.latitude

    @property
    def longitude(self) -> float | None:
        """Return the truck's longitude."""
        return self._location.longitude

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        truck = self.coordinator.truck_info or {}
        return {
            "route_name": self.coordinator.route_name,
            "car_no": truck.get("car_no"),
            "current_location": truck.get("current_location"),
            "current_rank": truck.get("current_rank"),
            "total_points": truck.get("total_points"),
        }

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": f"Trash Tracking {self.coordinator.route_name}",
            "manufacturer": "Logan",
            "model": "Garbage Truck Tracker",
            "sw_version": "2026.6.1b2",
        }
