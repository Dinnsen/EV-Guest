"""Button platform for EV Guest."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import SERVICE_CALCULATE, SERVICE_GRAB_CAR_DATA
from .entity import EVGuestCoordinatorEntity

PARALLEL_UPDATES = 0

BUTTONS = (
    ButtonEntityDescription(key=SERVICE_GRAB_CAR_DATA, icon="mdi:car-search"),
    ButtonEntityDescription(key=SERVICE_CALCULATE, icon="mdi:calculator"),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(EVGuestButton(coordinator, description) for description in BUTTONS)


class EVGuestButton(EVGuestCoordinatorEntity, ButtonEntity):
    """EV Guest action button."""

    entity_description: ButtonEntityDescription

    def __init__(self, coordinator, description: ButtonEntityDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    async def async_press(self) -> None:
        if self.entity_description.key == SERVICE_GRAB_CAR_DATA:
            await self.coordinator.async_lookup_car_data()
        else:
            await self.coordinator.async_calculate()
