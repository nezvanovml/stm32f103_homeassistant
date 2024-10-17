from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_IP_ADDRESS, CONF_NAME, Platform
from .stm_device import STMDevice, APIError, ConnectionError, InvalidMethod
from .const import DOMAIN, MANUFACTURER
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from datetime import timedelta
from typing import Any
from asyncio import timeout
import logging
from homeassistant.helpers.device_registry import DeviceInfo

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR, Platform.SWITCH, Platform.BUTTON, Platform.BINARY_SENSOR, Platform.NUMBER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    device = STMDevice(entry.data[CONF_IP_ADDRESS])
    coordinator = STMDeviceDataUpdateCoordinator(hass, device, await device.ip_address, await device.version)
    await coordinator.async_config_entry_first_refresh()
    entry.async_on_unload(entry.add_update_listener(update_listener))
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""
    await hass.config_entries.async_reload(entry.entry_id)


class STMDeviceDataUpdateCoordinator(
    DataUpdateCoordinator[dict[str, Any]]):  # pylint: disable=hass-enforce-coordinator-module
    """Class to manage fetching data API."""

    def __init__(self, hass: HomeAssistant, device: STMDevice, ip_address: str, version: int | None) -> None:
        """Initialize."""
        self.device = device
        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, ip_address)},
            manufacturer=MANUFACTURER,
            name=f"Controller_{ip_address.split('.')[-2]}_{ip_address.split('.')[-1]}",
            sw_version=version,
        )
        self.state = {}
        self.system_info = None

        update_interval = timedelta(seconds=5)

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            async with timeout(10):
                if not self.system_info:
                    self.system_info = await self.device.system_info
                current = await self.device.state
        except (APIError, ConnectionError, InvalidMethod) as error:
            raise UpdateFailed(error) from error
        _LOGGER.error(f"Loaded data: {current}")
        return current
