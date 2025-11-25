"""Sensor platform for Trash Tracking integration."""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TrashTrackingCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class TrashTrackingSensorEntityDescription(SensorEntityDescription):
    """Describes Trash Tracking sensor entity."""

    value_fn: Callable[[TrashTrackingCoordinator], Any] | None = None
    attr_fn: Callable[[TrashTrackingCoordinator], dict[str, Any]] | None = None


SENSORS: tuple[TrashTrackingSensorEntityDescription, ...] = (
    TrashTrackingSensorEntityDescription(
        key="status",
        name="Status",
        icon="mdi:truck",
        value_fn=lambda coordinator: coordinator.status,
        attr_fn=lambda coordinator: {
            "reason": coordinator.reason,
            "route_name": coordinator.route_name,
            "last_update": coordinator.data.get("timestamp") if coordinator.data else None,
            "enter_point": coordinator.enter_point_name,
            "exit_point": coordinator.exit_point_name,
            "schedule_weekdays": coordinator.schedule_weekdays,
            "schedule_time_start": coordinator.schedule_time_start,
            "schedule_time_end": coordinator.schedule_time_end,
        },
    ),
    TrashTrackingSensorEntityDescription(
        key="truck_info",
        name="Truck Info",
        icon="mdi:information",
        value_fn=lambda coordinator: (
            f"{coordinator.truck_info.get('current_location', 'Unknown')} "
            f"({coordinator.truck_info.get('current_rank', 0)}/{coordinator.truck_info.get('total_points', 0)})"
            if coordinator.truck_info
            else "No truck nearby"
        ),
        attr_fn=lambda coordinator: coordinator.truck_info if coordinator.truck_info else {},
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Trash Tracking sensors."""
    coordinator: TrashTrackingCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [TrashTrackingSensor(coordinator, description, entry) for description in SENSORS]

    async_add_entities(entities)


class TrashTrackingSensor(CoordinatorEntity[TrashTrackingCoordinator], SensorEntity):
    """Representation of a Trash Tracking sensor."""

    entity_description: TrashTrackingSensorEntityDescription

    def __init__(
        self,
        coordinator: TrashTrackingCoordinator,
        description: TrashTrackingSensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry

        # Generate unique ID
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_has_entity_name = True

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if self.entity_description.attr_fn:
            return self.entity_description.attr_fn(self.coordinator)
        return {}

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
