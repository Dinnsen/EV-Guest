"""Switch platform for EV Guest."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import INPUT_CONTINUOUS_CHARGING_PREFERRED, INPUT_USE_COMPLETION_TIME
from .coordinator import EVGuestConfigEntry
from .entity import EVGuestEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EVGuestConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        EVGuestInputSwitch(coordinator, key) for key in (INPUT_USE_COMPLETION_TIME, INPUT_CONTINUOUS_CHARGING_PREFERRED)
    )


class EVGuestInputSwitch(EVGuestEntity, SwitchEntity):
    """A planning option."""

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.inputs.get(self._key, True))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_input_value(self._key, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_input_value(self._key, False)
