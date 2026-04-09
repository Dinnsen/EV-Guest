"""Text platform for EV Guest."""

from __future__ import annotations

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import INPUT_LICENSE_PLATE
from .entity import EVGuestCoordinatorEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data["ev_guest"][entry.entry_id]
    async_add_entities([EVGuestText(coordinator)])


class EVGuestText(EVGuestCoordinatorEntity, TextEntity):
    """Representation of the EV Guest license plate text entity."""

    _attr_mode = TextMode.TEXT
    _attr_icon = "mdi:card-text-outline"
    _attr_native_max = 16

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, INPUT_LICENSE_PLATE, "License Plate")

    @property
    def native_value(self) -> str:
        return self.coordinator.data.inputs.get(self._key, "")

    async def async_set_value(self, value: str) -> None:
        await self.coordinator.async_set_input_value(self._key, value)
