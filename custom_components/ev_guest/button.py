"""Button platform for EV Guest."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import EVGuestCoordinatorEntity

BUTTONS = (
    ButtonEntityDescription(key="grab_car_data", name="Grab Car Data", icon="mdi:car-search"),
    ButtonEntityDescription(key="calculate", name="Calculate", icon="mdi:calculator"),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data["ev_guest"][entry.entry_id]
    async_add_entities(EVGuestButton(coordinator, description) for description in BUTTONS)


class EVGuestButton(EVGuestCoordinatorEntity, ButtonEntity):
    """Representation of an EV Guest button."""

    entity_description: ButtonEntityDescription

    def __init__(self, coordinator, description: ButtonEntityDescription) -> None:
        super().__init__(coordinator, description.key, description.name or description.key)
        self.entity_description = description

    async def async_press(self) -> None:
        if self.entity_description.key == "grab_car_data":
            await self.coordinator.async_lookup_car_data()
        elif self.entity_description.key == "calculate":
            await self.coordinator.async_calculate()
