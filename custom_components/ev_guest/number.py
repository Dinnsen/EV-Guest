"""Number platform for EV Guest."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, PERCENTAGE, UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    INPUT_BATTERY_CAPACITY,
    INPUT_CHARGE_LIMIT,
    INPUT_CHARGER_POWER,
    INPUT_SOC,
)
from .entity import EVGuestCoordinatorEntity

PARALLEL_UPDATES = 0

NUMBER_SPECS: dict[str, dict] = {
    INPUT_SOC: {
        "min": 0,
        "max": 100,
        "step": 1,
        "unit": PERCENTAGE,
        "icon": "mdi:battery-50",
        "entity_category": None,
    },
    INPUT_BATTERY_CAPACITY: {
        "min": 1,
        "max": 300,
        "step": 0.1,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "icon": "mdi:car-electric",
        "entity_category": None,
    },
    INPUT_CHARGER_POWER: {
        "min": 0.1,
        "max": 350,
        "step": 0.1,
        "unit": UnitOfPower.KILO_WATT,
        "icon": "mdi:ev-station",
        "entity_category": EntityCategory.CONFIG,
    },
    INPUT_CHARGE_LIMIT: {
        "min": 0,
        "max": 100,
        "step": 1,
        "unit": PERCENTAGE,
        "icon": "mdi:battery-arrow-up",
        "entity_category": None,
    },
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities([EVGuestNumber(coordinator, key) for key in NUMBER_SPECS])


class EVGuestNumber(EVGuestCoordinatorEntity, NumberEntity):
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator, key: str) -> None:
        super().__init__(coordinator, key)
        spec = NUMBER_SPECS[key]
        self._attr_native_min_value = spec["min"]
        self._attr_native_max_value = spec["max"]
        self._attr_native_step = spec["step"]
        self._attr_native_unit_of_measurement = spec["unit"]
        self._attr_icon = spec["icon"]
        self._attr_entity_category = spec["entity_category"]

    @property
    def native_value(self):
        return self.coordinator.data.inputs.get(self._key)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_input_value(self._key, float(value))
