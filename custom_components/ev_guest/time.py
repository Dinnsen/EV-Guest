"""Time platform for EV Guest."""

from __future__ import annotations

from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import INPUT_CHARGE_COMPLETION_TIME
from .coordinator import EVGuestConfigEntry, EVGuestCoordinator
from .entity import EVGuestEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EVGuestConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([EVGuestCompletionTime(entry.runtime_data)])


class EVGuestCompletionTime(EVGuestEntity, TimeEntity):
    """The time the car must be charged by."""

    def __init__(self, coordinator: EVGuestCoordinator) -> None:
        super().__init__(coordinator, INPUT_CHARGE_COMPLETION_TIME)

    @property
    def native_value(self) -> time:
        return self.coordinator.completion_time

    async def async_set_value(self, value: time) -> None:
        await self.coordinator.async_set_input_value(self._key, value)
