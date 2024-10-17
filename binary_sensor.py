from __future__ import annotations
from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from . import STMDeviceDataUpdateCoordinator
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import callback

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add AccuWeather entities from a config_entry."""

    coordinator: STMDeviceDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    binary_sensors = []
    if "button" in coordinator.system_info:
        for i in range(1, coordinator.system_info.get("button") + 1):
            binary_sensors.append(ButtonBinarySensor(coordinator, i))
    if "binary_sensor" in coordinator.system_info:
        for i in range(1, coordinator.system_info.get("binary_sensor") + 1):
            binary_sensors.append(SimpleBinarySensor(coordinator, i))
    if "v_binary_sensor" in coordinator.system_info:
        for i in range(1, coordinator.system_info.get("v_binary_sensor") + 1):
            binary_sensors.append(VirtualBinarySensor(coordinator, i))
    async_add_entities(binary_sensors)


class ButtonBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a binary sensor."""
    _attr_has_entity_name = True

    def __init__(self, coordinator, idx) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.idx = idx
        self._attr_unique_id = f"{coordinator.system_info['device_index']}_button_{idx}".lower()
        self._attr_device_info = coordinator.device_info
        self._attr_name = f"Кнопка {idx}"
        self._coordinator = coordinator
        self._attr_is_on = self._get_sensor_data(coordinator)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle data update."""
        self._attr_is_on = self._get_sensor_data(self._coordinator)
        self.async_write_ha_state()

    def _get_sensor_data(self, data):
        """Get sensor data."""
        if not "button" in data:
            return None
        if len(data["button"]) < self.idx:
            return None
        return bool(data["button"][(self.idx) - 1])


class SimpleBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a binary sensor."""
    _attr_has_entity_name = True

    def __init__(self, coordinator, idx) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.idx = idx
        self._attr_unique_id = f"{coordinator.system_info['device_index']}_binary_sensor_{idx}".lower()
        self._attr_device_info = coordinator.device_info
        self._attr_name = f"Бинарный сенсор {idx}"
        self._coordinator = coordinator
        self._attr_is_on = self._get_sensor_data(coordinator.data)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle data update."""
        self._attr_is_on = self._get_sensor_data(self._coordinator.data)
        self.async_write_ha_state()

    def _get_sensor_data(self, data):
        """Get sensor data."""
        if "binary_sensor" not in data:
            return None
        if len(data["binary_sensor"]) < self.idx:
            return None
        return bool(data["binary_sensor"][(self.idx) - 1])


class VirtualBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a binary sensor."""
    _attr_has_entity_name = True

    def __init__(self, coordinator, idx) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.idx = idx
        self._attr_unique_id = f"{coordinator.system_info['device_index']}_virtual_binary_sensor_{idx}".lower()
        self._attr_device_info = coordinator.device_info
        self._attr_name = f"Виртуальный бинарный сенсор {idx}"
        self._coordinator = coordinator
        self._attr_is_on = self._get_sensor_data(coordinator.data)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle data update."""
        self._attr_is_on = self._get_sensor_data(self._coordinator.data)
        self.async_write_ha_state()

    def _get_sensor_data(self, data):
        """Get sensor data."""
        if "v_binary_sensor" not in data:
            return None
        if len(data["v_binary_sensor"]) < self.idx:
            return None
        return bool(data["v_binary_sensor"][(self.idx) - 1])