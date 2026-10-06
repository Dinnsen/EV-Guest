"""Sensor platform for EV Guest."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.const import EntityCategory, UnitOfEnergy, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import (
    ATTR_CHARGING_SCHEDULE,
    ATTR_CHARGING_SEGMENTS,
    ATTR_ERROR_DETAIL,
    ATTR_FUEL_TYPE,
    ATTR_LAST_CALCULATION,
    ATTR_LAST_LOOKUP,
    ATTR_LAST_SOURCE,
    ATTR_MATCH_SCORE,
    ATTR_MODEL_YEAR,
    ATTR_PLAN_LOCKED,
    ATTR_PLAN_MODE,
    ATTR_RAW_TWO_DAYS,
    ATTR_VIN,
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
    STATUS_OPTIONS,
)
from .coordinator import EVGuestConfigEntry, EVGuestCoordinator
from .entity import EVGuestEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class EVGuestSensorEntityDescription(SensorEntityDescription):
    """Describes an EV Guest sensor."""

    value_fn: Callable[[EVGuestCoordinator], StateType | datetime]
    car_info: bool = False


def _result(key: str) -> Callable[[EVGuestCoordinator], StateType]:
    return lambda coordinator: coordinator.data.results.get(key)


SENSORS: tuple[EVGuestSensorEntityDescription, ...] = (
    EVGuestSensorEntityDescription(
        key=RESULT_CHARGING_SPEED,
        native_unit_of_measurement="%/h",
        suggested_display_precision=1,
        value_fn=_result(RESULT_CHARGING_SPEED),
    ),
    EVGuestSensorEntityDescription(
        key=RESULT_CHARGE_START_TIME,
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda coordinator: coordinator.plan_start,
    ),
    EVGuestSensorEntityDescription(
        key=RESULT_CHARGE_END_TIME,
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda coordinator: coordinator.plan_end,
    ),
    EVGuestSensorEntityDescription(
        key=RESULT_CHARGE_TIME,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_display_precision=0,
        value_fn=_result(RESULT_CHARGE_TIME),
    ),
    EVGuestSensorEntityDescription(
        key=RESULT_CHARGE_COSTS,
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
        value_fn=_result(RESULT_CHARGE_COSTS),
    ),
    EVGuestSensorEntityDescription(
        key=RESULT_STATUS,
        device_class=SensorDeviceClass.ENUM,
        options=STATUS_OPTIONS,
        value_fn=lambda coordinator: coordinator.status(),
    ),
    EVGuestSensorEntityDescription(
        key=RESULT_CAR_BRAND,
        entity_category=EntityCategory.DIAGNOSTIC,
        car_info=True,
        value_fn=_result(RESULT_CAR_BRAND),
    ),
    EVGuestSensorEntityDescription(
        key=RESULT_CAR_MODEL,
        entity_category=EntityCategory.DIAGNOSTIC,
        car_info=True,
        value_fn=_result(RESULT_CAR_MODEL),
    ),
    EVGuestSensorEntityDescription(
        key=RESULT_CAR_VARIANT,
        entity_category=EntityCategory.DIAGNOSTIC,
        car_info=True,
        value_fn=_result(RESULT_CAR_VARIANT),
    ),
    EVGuestSensorEntityDescription(
        key=RESULT_CAR_BATTERY_CAPACITY,
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        entity_category=EntityCategory.DIAGNOSTIC,
        car_info=True,
        value_fn=_result(RESULT_CAR_BATTERY_CAPACITY),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EVGuestConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(EVGuestSensor(coordinator, description) for description in SENSORS)


class EVGuestSensor(EVGuestEntity, SensorEntity):
    """EV Guest sensor."""

    entity_description: EVGuestSensorEntityDescription

    def __init__(self, coordinator: EVGuestCoordinator, description: EVGuestSensorEntityDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description
        if description.key == RESULT_CHARGE_COSTS:
            self._attr_native_unit_of_measurement = coordinator.currency

    @property
    def available(self) -> bool:
        if self.entity_description.car_info and not self.coordinator.data.service_health.get("motorapi", True):
            return False
        return super().available

    @property
    def native_value(self) -> StateType | datetime:
        return self.entity_description.value_fn(self.coordinator)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.key != RESULT_STATUS:
            return None
        results = self.coordinator.data.results
        return {
            ATTR_ERROR_DETAIL: self.coordinator.error_detail,
            ATTR_PLAN_MODE: results.get(ATTR_PLAN_MODE),
            ATTR_PLAN_LOCKED: self.coordinator.is_plan_locked(),
            ATTR_CHARGING_SEGMENTS: results.get(ATTR_CHARGING_SEGMENTS, []),
            ATTR_CHARGING_SCHEDULE: results.get(ATTR_CHARGING_SCHEDULE, []),
            ATTR_RAW_TWO_DAYS: results.get(ATTR_RAW_TWO_DAYS, []),
            ATTR_LAST_CALCULATION: results.get(ATTR_LAST_CALCULATION),
            ATTR_LAST_LOOKUP: results.get(ATTR_LAST_LOOKUP),
            ATTR_LAST_SOURCE: results.get(ATTR_LAST_SOURCE),
            ATTR_VIN: results.get(ATTR_VIN),
            ATTR_MODEL_YEAR: results.get(ATTR_MODEL_YEAR),
            ATTR_FUEL_TYPE: results.get(ATTR_FUEL_TYPE),
            ATTR_MATCH_SCORE: results.get(ATTR_MATCH_SCORE),
        }
