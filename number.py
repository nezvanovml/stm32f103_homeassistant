from __future__ import annotations
from homeassistant.components.number import NumberDeviceClass, NumberEntity, RestoreNumber
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

    numbers = []
    if "v_numeric" in coordinator.system_info:
        for i in range(1, coordinator.system_info.get("v_numeric") + 1):
            try:
                min_value = coordinator.system_info.get("v_numeric_min")[i-1]
                max_value = coordinator.system_info.get("v_numeric_max")[i-1]
            except Exception:
                min_value = 0
                max_value = 100
            numbers.append(VirtualNumber(coordinator, i, min_value, max_value))

    async_add_entities(numbers)


class VirtualNumber(CoordinatorEntity, RestoreNumber, NumberEntity):
    """Representation of a virtual numeric."""
    _attr_has_entity_name = True

    def __init__(self, coordinator, idx, min_value, max_value) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.idx = idx
        self._attr_unique_id = f"{coordinator.system_info['device_index']}_virtual_{idx}".lower()
        self._attr_device_info = coordinator.device_info
        self._attr_name = f"Виртуальное число {idx}"
        self._attr_native_step = 1
        self._coordinator = coordinator
        self._attr_native_value = self._get_numeric_data(coordinator.data)
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value


    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        await self._coordinator.device.api_request("v_numeric", "POST", {f"{self.idx}": int(value)})

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle data update."""
        self._attr_native_value = self._get_numeric_data(self._coordinator.data)
        self.async_write_ha_state()

    def _get_numeric_data(self, data):
        """Get number data."""
        if not "v_numeric" in data:
            return None
        if len(data["v_numeric"]) < self.idx:
            return None
        return float(data["v_numeric"][(self.idx) - 1])


    async def async_added_to_hass(self) -> None:
        """Restore on startup."""
        await super().async_added_to_hass()

        if not (await self.async_get_last_number_data()):
            return
        self._attr_native_value = self.native_value
        if self.native_value != 0:
            await self.async_set_native_value(self.native_value)