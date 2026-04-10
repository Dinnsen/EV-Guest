"""Switch platform for EV Guest."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import INPUT_USE_COMPLETION_TIME
from .entity import EVGuestCoordinatorEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities([EVGuestUseCompletionTimeSwitch(coordinator)])


class EVGuestUseCompletionTimeSwitch(EVGuestCoordinatorEntity, SwitchEntity):
    """Toggle whether completion time should be enforced."""

    _attr_icon = "mdi:clock-check-outline"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, INPUT_USE_COMPLETION_TIME)

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.inputs.get(self._key, True))

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_input_value(self._key, True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_input_value(self._key, False)
