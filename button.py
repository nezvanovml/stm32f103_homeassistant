from __future__ import annotations
from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from . import STMDeviceDataUpdateCoordinator
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add AccuWeather entities from a config_entry."""

    coordinator: STMDeviceDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    buttons = []
    if "relay" in coordinator.system_info:
        for i in range(1, coordinator.system_info.get("relay") + 1):
            buttons.append(RelayButton(coordinator, i))
    if "v_button" in coordinator.system_info:
        for i in range(1, coordinator.system_info.get("v_button") + 1):
            buttons.append(VirtualButton(coordinator, i))
    async_add_entities(buttons)


class RelayButton(CoordinatorEntity, ButtonEntity):
    """Representation of a button."""
    _attr_has_entity_name = True

    def __init__(self, coordinator, idx) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self.idx = idx
        self._attr_unique_id = f"{coordinator.system_info['device_index']}_relay_{idx}".lower()
        self._attr_device_info = coordinator.device_info
        self._attr_name = f"Импульс (Реле {idx})"
        self._coordinator = coordinator

    async def async_press(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        if "relay" in self._coordinator.system_info and  self._coordinator.system_info["relay"] >= self.idx:
            await self._coordinator.device.api_request("relay", "POST", {f"{self.idx}": "i"})
            await self._coordinator.async_request_refresh()

class VirtualButton(CoordinatorEntity, ButtonEntity):
    """Representation of a virtual button."""
    _attr_has_entity_name = True

    def __init__(self, coordinator, idx) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self.idx = idx
        self._attr_unique_id = f"{coordinator.system_info['device_index']}_virtual_{idx}".lower()
        self._attr_device_info = coordinator.device_info
        self._attr_name = f"Виртуальная кнопка {idx}"
        self._coordinator = coordinator

    async def async_press(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        if "v_button" in self._coordinator.system_info and self._coordinator.system_info["v_button"] >= self.idx:
            await self._coordinator.device.api_request("v_button", "POST", {f"{self.idx}": "1"})
            await self._coordinator.async_request_refresh()
