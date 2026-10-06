"""Number platform for EV Guest."""

from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import INPUT_BATTERY_CAPACITY, INPUT_CHARGE_LIMIT, INPUT_CHARGER_POWER, INPUT_SOC
from .coordinator import EVGuestConfigEntry, EVGuestCoordinator
from .entity import EVGuestEntity

PARALLEL_UPDATES = 0

NUMBERS: tuple[NumberEntityDescription, ...] = (
    NumberEntityDescription(
        key=INPUT_SOC,
        device_class=NumberDeviceClass.BATTERY,
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.BOX,
    ),
    NumberEntityDescription(
        key=INPUT_CHARGE_LIMIT,
        device_class=NumberDeviceClass.BATTERY,
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.BOX,
    ),
    NumberEntityDescription(
        key=INPUT_BATTERY_CAPACITY,
        device_class=NumberDeviceClass.ENERGY_STORAGE,
        native_min_value=1,
        native_max_value=300,
        native_step=0.1,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        mode=NumberMode.BOX,
    ),
    NumberEntityDescription(
        key=INPUT_CHARGER_POWER,
        device_class=NumberDeviceClass.POWER,
        native_min_value=0.1,
        native_max_value=350,
        native_step=0.1,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        entity_category=EntityCategory.CONFIG,
        mode=NumberMode.BOX,
    ),
)

# Kept for backwards compatibility with code that imports the input keys.
NUMBER_SPECS = {description.key: description for description in NUMBERS}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EVGuestConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(EVGuestNumber(coordinator, description) for description in NUMBERS)


class EVGuestNumber(EVGuestEntity, NumberEntity):
    """A planning input."""

    def __init__(self, coordinator: EVGuestCoordinator, description: NumberEntityDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.data.inputs.get(self._key)
        return float(value) if value is not None else None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_input_value(self._key, float(value))
