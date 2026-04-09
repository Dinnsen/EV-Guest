"""Sensor platform for EV Guest."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    RESULT_CAR_BATTERY_CAPACITY,
    RESULT_CAR_BRAND,
    RESULT_CAR_MODEL,
    RESULT_CAR_VARIANT,
    RESULT_CHARGE_COSTS,
    RESULT_CHARGE_END_TIME,
    RESULT_CHARGE_START_TIME,
    RESULT_CHARGE_TIME,
    RESULT_CHARGING_SPEED,
    RESULT_STATUS,
)
from .entity import EVGuestCoordinatorEntity

SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(key=RESULT_CHARGING_SPEED, name="Charging Speed", native_unit_of_measurement="%/h", icon="mdi:speedometer"),
    SensorEntityDescription(key=RESULT_CHARGE_START_TIME, name="Charge Start Time", icon="mdi:clock-start"),
    SensorEntityDescription(key=RESULT_CHARGE_END_TIME, name="Charge End Time", icon="mdi:clock-end"),
    SensorEntityDescription(key=RESULT_CHARGE_TIME, name="Charge Time", icon="mdi:timer-outline"),
    SensorEntityDescription(key=RESULT_CHARGE_COSTS, name="Charge Costs", device_class=SensorDeviceClass.MONETARY, icon="mdi:cash"),
    SensorEntityDescription(key=RESULT_CAR_BRAND, name="Car Brand", entity_category=EntityCategory.DIAGNOSTIC, icon="mdi:car-info"),
    SensorEntityDescription(key=RESULT_CAR_MODEL, name="Car Model", entity_category=EntityCategory.DIAGNOSTIC, icon="mdi:car-info"),
    SensorEntityDescription(key=RESULT_CAR_VARIANT, name="Car Variant", entity_category=EntityCategory.DIAGNOSTIC, icon="mdi:car-info"),
    SensorEntityDescription(key=RESULT_CAR_BATTERY_CAPACITY, name="Car Battery Capacity", native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, entity_category=EntityCategory.DIAGNOSTIC, icon="mdi:car-electric"),
    SensorEntityDescription(key=RESULT_STATUS, name="Status", entity_category=EntityCategory.DIAGNOSTIC, icon="mdi:information-outline"),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data["ev_guest"][entry.entry_id]
    async_add_entities(EVGuestSensor(coordinator, description) for description in SENSORS)


class EVGuestSensor(EVGuestCoordinatorEntity, SensorEntity):
    """Representation of an EV Guest sensor."""

    entity_description: SensorEntityDescription

    def __init__(self, coordinator, description: SensorEntityDescription) -> None:
        super().__init__(coordinator, description.key, description.name or description.key)
        self.entity_description = description
        if description.key == RESULT_CHARGE_COSTS:
            self._attr_native_unit_of_measurement = coordinator.currency

    @property
    def native_value(self):
        return self.coordinator.data.results.get(self.entity_description.key)
