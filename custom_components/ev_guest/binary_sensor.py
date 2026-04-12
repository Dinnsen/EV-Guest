"""Binary sensor platform for EV Guest."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DIAGNOSTIC_CHARGE_NOW
from .entity import EVGuestCoordinatorEntity

PARALLEL_UPDATES = 0

BINARY_SENSORS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key=DIAGNOSTIC_CHARGE_NOW,
        icon="mdi:lightning-bolt-circle",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(EVGuestBinarySensor(coordinator, description) for description in BINARY_SENSORS)


class EVGuestBinarySensor(EVGuestCoordinatorEntity, BinarySensorEntity):
    """EV Guest binary sensor."""

    entity_description: BinarySensorEntityDescription

    def __init__(self, coordinator, description: BinarySensorEntityDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        if self.entity_description.key == DIAGNOSTIC_CHARGE_NOW:
            return self.coordinator.is_charge_now()
        return None
