"""Text platform for EV Guest."""

from __future__ import annotations

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import INPUT_LICENSE_PLATE
from .coordinator import EVGuestConfigEntry, EVGuestCoordinator
from .entity import EVGuestEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EVGuestConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([EVGuestLicensePlateText(entry.runtime_data)])


class EVGuestLicensePlateText(EVGuestEntity, TextEntity):
    """The guest car's license plate."""

    _attr_mode = TextMode.TEXT
    _attr_native_max = 16

    def __init__(self, coordinator: EVGuestCoordinator) -> None:
        super().__init__(coordinator, INPUT_LICENSE_PLATE)

    @property
    def native_value(self) -> str:
        return str(self.coordinator.data.inputs.get(self._key) or "")

    async def async_set_value(self, value: str) -> None:
        await self.coordinator.async_set_input_value(self._key, value.strip().upper())
