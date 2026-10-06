"""Button platform for EV Guest."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import SERVICE_CALCULATE, SERVICE_GRAB_CAR_DATA
from .coordinator import EVGuestConfigEntry
from .entity import EVGuestEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EVGuestConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(EVGuestButton(coordinator, key) for key in (SERVICE_GRAB_CAR_DATA, SERVICE_CALCULATE))


class EVGuestButton(EVGuestEntity, ButtonEntity):
    """Runs a lookup or a calculation."""

    async def async_press(self) -> None:
        if self._key == SERVICE_GRAB_CAR_DATA:
            await self.coordinator.async_lookup_car_data()
        else:
            await self.coordinator.async_calculate()
