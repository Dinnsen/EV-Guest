"""Text platform for EV Guest."""

from __future__ import annotations

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import INPUT_CHARGE_COMPLETION_TIME, INPUT_LICENSE_PLATE
from .entity import EVGuestCoordinatorEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [EVGuestLicensePlateText(coordinator), EVGuestCompletionTimeText(coordinator)]
    )


class EVGuestLicensePlateText(EVGuestCoordinatorEntity, TextEntity):
    _attr_name = "License Plate"
    _attr_mode = TextMode.TEXT
    _attr_icon = "mdi:card-text-outline"
    _attr_native_max = 16

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, INPUT_LICENSE_PLATE)

    @property
    def native_value(self) -> str:
        return self.coordinator.data.inputs.get(self._key, "")

    async def async_set_value(self, value: str) -> None:
        await self.coordinator.async_set_input_value(self._key, value)


class EVGuestCompletionTimeText(EVGuestCoordinatorEntity, TextEntity):
    _attr_name = "Charge Completion Time"
    _attr_mode = TextMode.TEXT
    _attr_icon = "mdi:clock-check-outline"
    _attr_native_max = 8

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, INPUT_CHARGE_COMPLETION_TIME)

    @property
    def native_value(self) -> str:
        return self.coordinator.get_completion_time_text()

    async def async_set_value(self, value: str) -> None:
        await self.coordinator.async_set_input_value(self._key, value)
