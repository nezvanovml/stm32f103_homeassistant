from __future__ import annotations

import datetime as dt

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_IP_ADDRESS, CONF_NAME, Platform
from .stm_device import STMDevice, APIError, ConnectionError, InvalidMethod
from .const import DOMAIN, MANUFACTURER
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from typing import Any
from asyncio import timeout, TimeoutError
import logging
from homeassistant.helpers.device_registry import DeviceInfo

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR, Platform.SWITCH, Platform.BUTTON, Platform.BINARY_SENSOR, Platform.NUMBER,
             Platform.DATETIME]


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
        self.ip_address = ip_address
        self.connection_error = False
        self.seconds_since_start = 0
        self.works_since = None
        update_interval = dt.timedelta(seconds=2)

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            async with timeout(5):
                if not self.system_info:
                    self.system_info = await self.device.system_info
                current = await self.device.state
        except (APIError, ConnectionError, InvalidMethod, TimeoutError) as error:
            _LOGGER.warning(f"Unable to fetch data from {self.ip_address}.")
            raise UpdateFailed(error) from error
        _LOGGER.info(f"Loaded data: {current}")

        # check seconds_since_start
        if "up" in current:
            seconds_since_start = int(current["up"])

            if not self.works_since:
                self.works_since = dt.datetime.now(dt.UTC) - dt.timedelta(
                    seconds=seconds_since_start)

            if seconds_since_start < self.seconds_since_start:
                # device restarted, need restoring state
                await self.restore_controller_state()
                self.works_since = dt.datetime.now(dt.UTC) - dt.timedelta(
                    seconds=seconds_since_start)

            self.seconds_since_start = seconds_since_start
        self.state = current
        return current

    async def restore_controller_state(self):
        _LOGGER.warning((f"Restoring {await self.device.ip_address} to {self.state}"))
        if "v_numeric" in self.state:
            i = 1
            params = {}
            for value in self.state["v_numeric"]:
                params[f"{i}"] = int(value)
                i += 1
            await self.device.api_request("v_numeric", "POST", params)

        if "v_switch" in self.state:
            i = 1
            params = {}
            for value in self.state["v_switch"]:
                params[f"{i}"] = int(value)
                i += 1
            await self.device.api_request("v_switch", "POST", params)

        if "relay" in self.state:
            i = 1
            params = {}
            for value in self.state["relay"]:
                params[f"{i}"] = int(value)
                i += 1
            await self.device.api_request("relay", "POST", params)
