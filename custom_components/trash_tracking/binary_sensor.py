"""Binary sensor platform for Trash Tracking."""
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL, STATE_NEARBY
from .coordinator import TrashTrackingCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Trash Tracking binary sensor platform."""
    coordinator: TrashTrackingCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [TrashTruckNearbyBinarySensor(coordinator, entry)]

    async_add_entities(entities)
    _LOGGER.info("Added %d binary sensor entities", len(entities))


class TrashTruckNearbyBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """垃圾車接近二元感測器 - 當垃圾車接近時為 ON."""

    _attr_device_class = BinarySensorDeviceClass.PRESENCE

    def __init__(
        self,
        coordinator: TrashTrackingCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)

        self._attr_unique_id = f"{entry.entry_id}_nearby"
        self._attr_name = "垃圾車接近"
        self._attr_icon = "mdi:bell-ring"
        self._attr_has_entity_name = True

        # Device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="垃圾車追蹤系統",
            manufacturer=MANUFACTURER,
            model=MODEL,
            configuration_url=coordinator.api_url,
        )

    @property
    def is_on(self) -> bool:
        """Return true if the truck is nearby."""
        return self.coordinator.data.get("status") == STATE_NEARBY

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        """Return additional attributes."""
        truck = self.coordinator.data.get("truck")
        if not truck:
            return {}

        return {
            "路線名稱": truck.get("line_name"),
            "車牌號碼": truck.get("car_no"),
        }
