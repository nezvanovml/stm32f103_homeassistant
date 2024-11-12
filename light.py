from __future__ import annotations
from homeassistant.components.light import LightDeviceClass, LightEntity, ColorMode
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

    lights = []
    if "light" in coordinator.system_info:
        for i in range(1, coordinator.system_info.get("light") + 1):
            lights.append(RelayLight(coordinator, i))
    async_add_entities(lights)


class RelayLight(CoordinatorEntity, LightEntity):
    """Representation of a light."""
    _attr_has_entity_name = True

    def __init__(self, coordinator, idx) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.idx = idx
        self._attr_unique_id = f"{coordinator.system_info['device_index']}_light_{idx}".lower()
        self._attr_device_info = coordinator.device_info
        self._attr_name = f"Освещение {idx}"
        self._coordinator = coordinator
        self._attr_is_on = self._get_light_data(coordinator.data)
        self._attr_color_mode = ColorMode.ONOFF

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        if "light" in self._coordinator.system_info and self._coordinator.system_info["light"] >= self.idx:
            await self._coordinator.device.api_request("light", "POST", {f"{self.idx}": 1})
            await self._coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        if "light" in self._coordinator.system_info and self._coordinator.system_info["light"] >= self.idx:
            await self._coordinator.device.api_request("light", "POST", {f"{self.idx}": 0})
            await self._coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle data update."""
        self._attr_is_on = self._get_light_data(self._coordinator.data)
        self.async_write_ha_state()

    def _get_light_data(self, data):
        """Get switch data."""
        if "light" not in data:
            return None
        if len(data["light"]) < self.idx:
            return None
        return bool(data["light"][(self.idx) - 1])
