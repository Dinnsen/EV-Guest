"""Number platform for EV Guest."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import *
from .entity import EVGuestCoordinatorEntity

PARALLEL_UPDATES = 0

@dataclass(frozen=True, kw_only=True)
class EVGuestNumberDescription:
    key: str
    native_min_value: float
    native_max_value: float
    native_step: float
    native_unit_of_measurement: str | None = None
    icon: str | None = None
    device_class: NumberDeviceClass | None = None

NUMBERS = (
    EVGuestNumberDescription(key=INPUT_SOC, native_min_value=0, native_max_value=100, native_step=1, native_unit_of_measurement=PERCENTAGE, icon="mdi:battery-50"),
    EVGuestNumberDescription(key=INPUT_BATTERY_CAPACITY, native_min_value=1, native_max_value=300, native_step=0.1, native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, icon="mdi:car-electric"),
    EVGuestNumberDescription(key=INPUT_CHARGER_POWER, native_min_value=0.1, native_max_value=350, native_step=0.1, native_unit_of_measurement=UnitOfPower.KILO_WATT, icon="mdi:ev-station"),
    EVGuestNumberDescription(key=INPUT_CHARGE_LIMIT, native_min_value=0, native_max_value=100, native_step=1, native_unit_of_measurement=PERCENTAGE, icon="mdi:battery-arrow-up"),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(EVGuestNumber(coordinator, description) for description in NUMBERS)


class EVGuestNumber(EVGuestCoordinatorEntity, NumberEntity):
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator, description: EVGuestNumberDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_native_min_value = description.native_min_value
        self._attr_native_max_value = description.native_max_value
        self._attr_native_step = description.native_step
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_icon = description.icon
        self._attr_device_class = description.device_class

    @property
    def native_value(self):
        return self.coordinator.data.inputs.get(self._key)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_input_value(self._key, float(value))
