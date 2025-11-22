"""Sensor platform for Trash Tracking."""
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_AREA,
    ATTR_ARRIVAL_DIFF,
    ATTR_CAR_NO,
    ATTR_CURRENT_LOCATION,
    ATTR_CURRENT_RANK,
    ATTR_ENTER_POINT,
    ATTR_EXIT_POINT,
    ATTR_LINE_NAME,
    ATTR_REASON,
    ATTR_TOTAL_POINTS,
    DOMAIN,
    MANUFACTURER,
    MODEL,
)
from .coordinator import TrashTrackingCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Trash Tracking sensor platform."""
    coordinator: TrashTrackingCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        TrashTrackingStatusSensor(coordinator, entry),
        TrashTrackingTruckInfoSensor(coordinator, entry),
    ]

    async_add_entities(entities)
    _LOGGER.info("Added %d sensor entities", len(entities))


class TrashTrackingStatusSensor(CoordinatorEntity, SensorEntity):
    """垃圾車狀態感測器 - 顯示 idle/nearby 狀態."""

    def __init__(
        self,
        coordinator: TrashTrackingCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_name = "垃圾車狀態"
        self._attr_icon = "mdi:trash-can"
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
    def state(self) -> str | None:
        """Return the state of the sensor."""
        return self.coordinator.data.get("status")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = {
            ATTR_REASON: self.coordinator.data.get("reason"),
        }

        truck = self.coordinator.data.get("truck")
        if truck:
            attrs[ATTR_LINE_NAME] = truck.get("line_name")
            attrs[ATTR_CAR_NO] = truck.get("car_no")
            attrs[ATTR_CURRENT_RANK] = truck.get("current_rank")
            attrs[ATTR_TOTAL_POINTS] = truck.get("total_points")
            attrs[ATTR_ARRIVAL_DIFF] = truck.get("arrival_diff")
            attrs[ATTR_AREA] = truck.get("area")
            attrs[ATTR_CURRENT_LOCATION] = truck.get("current_location")

            if enter_point := truck.get("enter_point"):
                attrs[ATTR_ENTER_POINT] = enter_point.get("name")

            if exit_point := truck.get("exit_point"):
                attrs[ATTR_EXIT_POINT] = exit_point.get("name")

        return attrs


class TrashTrackingTruckInfoSensor(CoordinatorEntity, SensorEntity):
    """垃圾車資訊感測器 - 顯示路線和車牌資訊."""

    def __init__(
        self,
        coordinator: TrashTrackingCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._attr_unique_id = f"{entry.entry_id}_truck_info"
        self._attr_name = "垃圾車資訊"
        self._attr_icon = "mdi:truck"
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
    def state(self) -> str | None:
        """Return the state of the sensor."""
        truck = self.coordinator.data.get("truck")
        if truck:
            line_name = truck.get("line_name", "未知路線")
            car_no = truck.get("car_no", "")
            return f"{line_name} ({car_no})" if car_no else line_name
        return "無垃圾車"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        truck = self.coordinator.data.get("truck")
        if not truck:
            return {}

        attrs = {
            "路線名稱": truck.get("line_name"),
            "車牌號碼": truck.get("car_no"),
            "當前站點": truck.get("current_rank"),
            "總站點數": truck.get("total_points"),
            "區域": truck.get("area"),
            "當前位置": truck.get("current_location"),
        }

        # 延遲時間
        if (arrival_diff := truck.get("arrival_diff")) is not None:
            if arrival_diff > 0:
                attrs["延遲時間"] = f"晚 {arrival_diff} 分鐘"
            elif arrival_diff < 0:
                attrs["延遲時間"] = f"早 {abs(arrival_diff)} 分鐘"
            else:
                attrs["延遲時間"] = "準時"

        # 收集點資訊
        if enter_point := truck.get("enter_point"):
            attrs["進入點"] = enter_point.get("name")
            attrs["進入點時間"] = enter_point.get("point_time")

        if exit_point := truck.get("exit_point"):
            attrs["離開點"] = exit_point.get("name")
            attrs["離開點時間"] = exit_point.get("point_time")

        return attrs
