from __future__ import annotations
from homeassistant.components.datetime import DateTimeEntity
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from . import STMDeviceDataUpdateCoordinator
import logging
import datetime

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

    datetimes = []

    datetimes.append(WorksSinceDateTime(coordinator))

    async_add_entities(datetimes)


class WorksSinceDateTime(CoordinatorEntity, DateTimeEntity):
    """Representation of a worsk since datetime."""
    _attr_has_entity_name = True

    def __init__(self, coordinator) -> None:
        """Initialize the datetime."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.system_info['device_index']}_works_since".lower()
        self._attr_device_info = coordinator.device_info
        self._attr_name = f"Старт работы"
        self._coordinator = coordinator
        self._attr_native_value = self._coordinator.works_since
        self._attr_assumed_state = True

    async def async_set_value(self, value: datetime) -> None:
        """Update the current value."""
        pass

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle data update."""
        self._attr_native_value = self._coordinator.works_since
        self.async_write_ha_state()
