from __future__ import annotations
from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
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

    switches = []
    if "relay" in coordinator.system_info:
        for i in range(1, coordinator.system_info.get("relay") + 1):
            switches.append(RelaySwitch(coordinator, i))
    if "virtual_switch" in coordinator.system_info:
        for i in range(1, coordinator.system_info.get("virtual_switch") + 1):
            switches.append(VirtualSwitch(coordinator, i))
    async_add_entities(switches)


class RelaySwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a switch."""
    _attr_has_entity_name = True

    def __init__(self, coordinator, idx) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.idx = idx
        self._attr_unique_id = f"{coordinator.system_info['device_index']}_relay_{idx}".lower()
        self._attr_device_info = coordinator.device_info
        self._attr_name = f"Реле {idx}"
        self._coordinator = coordinator
        self._attr_is_on = self._get_switch_data(coordinator.data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        if "relay" in self._coordinator.system_info and self._coordinator.system_info["relay"] >= self.idx:
            await self._coordinator.device.api_request("relay", "POST", {f"{self.idx}": 1})
            await self._coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        if "relay" in self._coordinator.system_info and self._coordinator.system_info["relay"] >= self.idx:
            await self._coordinator.device.api_request("relay", "POST", {f"{self.idx}": 0})
            await self._coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle data update."""
        self._attr_is_on = self._get_switch_data(self._coordinator.data)
        self.async_write_ha_state()

    def _get_switch_data(self, data):
        """Get switch data."""
        if not "relay" in data:
            return None
        if len(data["relay"]) < self.idx:
            return None
        return bool(data["relay"][(self.idx) - 1])

class VirtualSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a virtual switch."""
    _attr_has_entity_name = True

    def __init__(self, coordinator, idx) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.idx = idx
        self._attr_unique_id = f"{coordinator.system_info['device_index']}_virtual_{idx}".lower()
        self._attr_device_info = coordinator.device_info
        self._attr_name = f"Виртуальный выключатель {idx}"
        self._coordinator = coordinator
        self._attr_is_on = self._get_switch_data(coordinator.data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._coordinator.device.api_request("virtual_switch", "POST", {f"{self.idx}": 1})
        await self._coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        await self._coordinator.device.api_request("virtual_switch", "POST", {f"{self.idx}": 0})
        await self._coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle data update."""
        self._attr_is_on = self._get_switch_data(self._coordinator.data)
        self.async_write_ha_state()

    def _get_switch_data(self, data):
        """Get switch data."""
        if not "virtual_switch" in data:
            return None
        if len(data["virtual_switch"]) < self.idx:
            return None
        return bool(data["virtual_switch"][(self.idx) - 1])
