from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (UnitOfTemperature)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import STMDeviceDataUpdateCoordinator
from .const import DOMAIN


async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add AccuWeather entities from a config_entry."""

    coordinator: STMDeviceDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = []
    if "temperature" in coordinator.system_info:
        for addr in coordinator.system_info["temperature"]["addr"]:
            sensors.append(TemperatureSensor(coordinator, addr))
    if "analog_in" in coordinator.system_info:
        for i in range(1, coordinator.system_info.get("analog_in") + 1):
            sensors.append(AnalogInSensor(coordinator, i))
    if "counter" in coordinator.system_info:
        for i in range(1, coordinator.system_info.get("counter") + 1):
            sensors.append(MeterSensor(coordinator, i))
    async_add_entities(sensors)


class TemperatureSensor(CoordinatorEntity, SensorEntity):
    """Define an Temperature entity."""
    _attr_has_entity_name = True

    def __init__(
            self,
            coordinator: STMDeviceDataUpdateCoordinator,
            one_wire_addr: str,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.system_info['device_index']}_ds18b20_{one_wire_addr}".lower()
        self._attr_device_info = coordinator.device_info
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_name = f"Температура ({one_wire_addr})"
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._one_wire_addr = one_wire_addr
        self._attr_native_value = self._get_sensor_data(coordinator.data)
        self._coordinator = coordinator

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle data update."""
        self._attr_native_value = self._get_sensor_data(self._coordinator.data)
        self.async_write_ha_state()

    def _get_sensor_data(self, data):
        """Get sensor data."""
        if not "temperature" in data:
            return None
        if not self._one_wire_addr in data["temperature"]:
            return None
        return data["temperature"][self._one_wire_addr]


class AnalogInSensor(CoordinatorEntity, SensorEntity):
    """Define an Analog input entity."""
    _attr_has_entity_name = True

    def __init__(self, coordinator, idx) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.idx = idx
        self._attr_unique_id = f"{coordinator.system_info['device_index']}_analog_in_{idx}".lower()
        self._attr_device_info = coordinator.device_info
        self._attr_name = f"Аналоговый вход ({idx})"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_value = self._get_sensor_data(coordinator.data)
        self._coordinator = coordinator

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle data update."""
        self._attr_native_value = self._get_sensor_data(self._coordinator.data)
        self.async_write_ha_state()

    def _get_sensor_data(self, data):
        """Get sensor data."""
        if not "analog_in" in data:
            return None
        if len(data["analog_in"]) < self.idx:
            return None
        return data["analog_in"][(self.idx) - 1]


class MeterSensor(CoordinatorEntity, SensorEntity):
    """Define an Meter entity."""
    _attr_has_entity_name = True

    def __init__(
            self,
            coordinator: STMDeviceDataUpdateCoordinator,
            idx: int,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.system_info['device_index']}_counter_{idx}".lower()
        self._attr_device_info = coordinator.device_info
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_name = f"Счётчик ({idx})"
        # self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self.idx = idx
        self._attr_native_value = self._get_sensor_data(coordinator.data)
        self._coordinator = coordinator

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle data update."""
        self._attr_native_value = self._get_sensor_data(self._coordinator.data)
        self.async_write_ha_state()

    def _get_sensor_data(self, data):
        """Get sensor data."""
        if not "counter" in data:
            return None
        if len(data["counter"]) < self.idx:
            return None
        return data["counter"][(self.idx) - 1]
