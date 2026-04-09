"""Time platform for EV Guest."""

from __future__ import annotations

from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import INPUT_CHARGE_COMPLETION_TIME
from .entity import EVGuestCoordinatorEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities([EVGuestCompletionTime(coordinator)])


class EVGuestCompletionTime(EVGuestCoordinatorEntity, TimeEntity):
    _attr_icon = "mdi:clock-check-outline"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, INPUT_CHARGE_COMPLETION_TIME)

    @property
    def native_value(self) -> time:
        return self.coordinator.data.inputs[self._key]

    async def async_set_value(self, value: time) -> None:
        await self.coordinator.async_set_input_value(self._key, value)
