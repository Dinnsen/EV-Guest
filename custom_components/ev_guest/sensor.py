"""Sensor platform for EV Guest."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import *
from .entity import EVGuestCoordinatorEntity

PARALLEL_UPDATES = 0

SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(key=RESULT_CHARGING_SPEED, device_class=None, native_unit_of_measurement="%/h", icon="mdi:speedometer"),
    SensorEntityDescription(key=RESULT_CHARGE_START_TIME, icon="mdi:clock-start"),
    SensorEntityDescription(key=RESULT_CHARGE_END_TIME, icon="mdi:clock-end"),
    SensorEntityDescription(key=RESULT_CHARGE_TIME, icon="mdi:timer-outline"),
    SensorEntityDescription(key=RESULT_CHARGE_COSTS, device_class=SensorDeviceClass.MONETARY, icon="mdi:cash"),
    SensorEntityDescription(key=RESULT_CAR_BRAND, entity_category=EntityCategory.DIAGNOSTIC, icon="mdi:car-info"),
    SensorEntityDescription(key=RESULT_CAR_MODEL, entity_category=EntityCategory.DIAGNOSTIC, icon="mdi:car-info"),
    SensorEntityDescription(key=RESULT_CAR_VARIANT, entity_category=EntityCategory.DIAGNOSTIC, icon="mdi:car-info"),
    SensorEntityDescription(key=RESULT_CAR_BATTERY_CAPACITY, native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, entity_category=EntityCategory.DIAGNOSTIC, icon="mdi:car-electric"),
    SensorEntityDescription(key=RESULT_STATUS, entity_category=EntityCategory.DIAGNOSTIC, icon="mdi:information-outline"),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(EVGuestSensor(coordinator, description) for description in SENSORS)


class EVGuestSensor(EVGuestCoordinatorEntity, SensorEntity):
    """EV Guest sensor."""

    entity_description: SensorEntityDescription

    def __init__(self, coordinator, description: SensorEntityDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description
        if description.key == RESULT_CHARGE_COSTS:
            self._attr_native_unit_of_measurement = coordinator.currency

    @property
    def available(self) -> bool:
        if self.entity_description.key in {
            RESULT_CAR_BRAND,
            RESULT_CAR_MODEL,
            RESULT_CAR_VARIANT,
            RESULT_CAR_BATTERY_CAPACITY,
        } and not self.coordinator.data.service_health.get("motorapi", True):
            return False
        return True

    @property
    def extra_state_attributes(self):
        if self.entity_description.key != RESULT_STATUS:
            return None
        return {
            ATTR_LAST_LOOKUP: self.coordinator.data.results.get(ATTR_LAST_LOOKUP),
            ATTR_LAST_CALCULATION: self.coordinator.data.results.get(ATTR_LAST_CALCULATION),
            ATTR_LAST_SOURCE: self.coordinator.data.results.get(ATTR_LAST_SOURCE),
            ATTR_VIN: self.coordinator.data.results.get(ATTR_VIN),
            ATTR_MODEL_YEAR: self.coordinator.data.results.get(ATTR_MODEL_YEAR),
            ATTR_FUEL_TYPE: self.coordinator.data.results.get(ATTR_FUEL_TYPE),
            ATTR_MATCH_SCORE: self.coordinator.data.results.get(ATTR_MATCH_SCORE),
        }

    @property
    def native_value(self):
        return self.coordinator.data.results.get(self.entity_description.key)
