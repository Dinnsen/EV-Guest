"""Binary sensor platform for EV Guest."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DIAGNOSTIC_CHARGE_NOW
from .coordinator import EVGuestConfigEntry, EVGuestCoordinator
from .entity import EVGuestEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EVGuestConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([EVGuestChargeNowBinarySensor(entry.runtime_data)])


class EVGuestChargeNowBinarySensor(EVGuestEntity, BinarySensorEntity):
    """On exactly while the current time is inside a planned charging segment."""

    def __init__(self, coordinator: EVGuestCoordinator) -> None:
        super().__init__(coordinator, DIAGNOSTIC_CHARGE_NOW)

    @property
    def is_on(self) -> bool:
        return self.coordinator.is_charge_now()
