"""Sensor platform for EV Guest."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_CHARGER_BACKEND,
    ATTR_CHARGER_COMMANDABLE,
    ATTR_CHARGER_CONTROL_ENABLED,
    ATTR_CHARGER_ENTITY,
    ATTR_CHARGER_EXPECTED_ON,
    ATTR_CHARGER_MISMATCH,
    ATTR_CHARGER_STATUS_ENTITY,
    ATTR_CHARGING_SCHEDULE,
    ATTR_CONTROL_TICK_INTERVAL,
    ATTR_DUMMY_CHARGER,
    ATTR_FUEL_TYPE,
    ATTR_LAST_CALCULATION,
    ATTR_LAST_LOOKUP,
    ATTR_LAST_SOURCE,
    ATTR_LAST_CHARGER_COMMAND_AT,
    ATTR_LAST_CHARGER_COMMAND_REASON,
    ATTR_MATCH_SCORE,
    ATTR_MODEL_YEAR,
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
    RESULT_CHARGER_ACTIVE_WINDOW,
    RESULT_CHARGER_ACTUAL_STATE,
    RESULT_CHARGER_BACKEND,
    RESULT_CHARGER_LAST_COMMAND,
    RESULT_CHARGER_LAST_RESULT,
    RESULT_CHARGER_NEXT_START,
    RESULT_CHARGER_NEXT_STOP,
    RESULT_CHARGER_TARGET_STATE,
    RESULT_CHARGING_SPEED,
    RESULT_STATUS,
)
from .entity import EVGuestCoordinatorEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class EVGuestSensorDescription(SensorEntityDescription):
    result_key: str
    is_status_attributes: bool = False
    use_currency: bool = False


SENSORS: tuple[EVGuestSensorDescription, ...] = (
    EVGuestSensorDescription(
        key=RESULT_CHARGING_SPEED,
        result_key=RESULT_CHARGING_SPEED,
        native_unit_of_measurement="%/h",
        icon="mdi:speedometer",
    ),
    EVGuestSensorDescription(
        key=RESULT_CHARGE_START_TIME,
        result_key=RESULT_CHARGE_START_TIME,
        icon="mdi:clock-start",
    ),
    EVGuestSensorDescription(
        key=RESULT_CHARGE_END_TIME,
        result_key=RESULT_CHARGE_END_TIME,
        icon="mdi:clock-end",
    ),
    EVGuestSensorDescription(
        key=RESULT_CHARGE_TIME,
        result_key=RESULT_CHARGE_TIME,
        icon="mdi:timer-outline",
    ),
    EVGuestSensorDescription(
        key=RESULT_CHARGE_COSTS,
        result_key=RESULT_CHARGE_COSTS,
        device_class=SensorDeviceClass.MONETARY,
        icon="mdi:cash",
        use_currency=True,
    ),
    EVGuestSensorDescription(
        key=RESULT_CAR_BRAND,
        result_key=RESULT_CAR_BRAND,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:car-info",
    ),
    EVGuestSensorDescription(
        key=RESULT_CAR_MODEL,
        result_key=RESULT_CAR_MODEL,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:car-info",
    ),
    EVGuestSensorDescription(
        key=RESULT_CAR_VARIANT,
        result_key=RESULT_CAR_VARIANT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:car-info",
    ),
    EVGuestSensorDescription(
        key=RESULT_CAR_BATTERY_CAPACITY,
        result_key=RESULT_CAR_BATTERY_CAPACITY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:car-electric",
    ),
    EVGuestSensorDescription(
        key=RESULT_STATUS,
        result_key=RESULT_STATUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:information-outline",
        is_status_attributes=True,
    ),
    EVGuestSensorDescription(
        key=RESULT_CHARGER_BACKEND,
        result_key=RESULT_CHARGER_BACKEND,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:ev-plug-type",
    ),
    EVGuestSensorDescription(
        key=RESULT_CHARGER_TARGET_STATE,
        result_key=RESULT_CHARGER_TARGET_STATE,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:target",
    ),
    EVGuestSensorDescription(
        key=RESULT_CHARGER_ACTUAL_STATE,
        result_key=RESULT_CHARGER_ACTUAL_STATE,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:toggle-switch",
    ),
    EVGuestSensorDescription(
        key=RESULT_CHARGER_LAST_COMMAND,
        result_key=RESULT_CHARGER_LAST_COMMAND,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:history",
    ),
    EVGuestSensorDescription(
        key=RESULT_CHARGER_LAST_RESULT,
        result_key=RESULT_CHARGER_LAST_RESULT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:message-text-outline",
    ),
    EVGuestSensorDescription(
        key=RESULT_CHARGER_NEXT_START,
        result_key=RESULT_CHARGER_NEXT_START,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:play-outline",
    ),
    EVGuestSensorDescription(
        key=RESULT_CHARGER_NEXT_STOP,
        result_key=RESULT_CHARGER_NEXT_STOP,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:stop-outline",
    ),
    EVGuestSensorDescription(
        key=RESULT_CHARGER_ACTIVE_WINDOW,
        result_key=RESULT_CHARGER_ACTIVE_WINDOW,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:calendar-range",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(EVGuestSensor(coordinator, description) for description in SENSORS)


class EVGuestSensor(EVGuestCoordinatorEntity, SensorEntity):
    """EV Guest sensor."""

    entity_description: EVGuestSensorDescription

    def __init__(self, coordinator, description: EVGuestSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description
        if description.use_currency:
            self._attr_native_unit_of_measurement = coordinator.currency

    @property
    def available(self) -> bool:
        if self.entity_description.result_key in {
            RESULT_CAR_BRAND,
            RESULT_CAR_MODEL,
            RESULT_CAR_VARIANT,
            RESULT_CAR_BATTERY_CAPACITY,
        } and not self.coordinator.data.service_health.get("motorapi", True):
            return False
        return True

    @property
    def extra_state_attributes(self):
        if not self.entity_description.is_status_attributes:
            return None
        return {
            ATTR_LAST_LOOKUP: self.coordinator.data.results.get(ATTR_LAST_LOOKUP),
            ATTR_LAST_CALCULATION: self.coordinator.data.results.get(ATTR_LAST_CALCULATION),
            ATTR_LAST_SOURCE: self.coordinator.data.results.get(ATTR_LAST_SOURCE),
            ATTR_VIN: self.coordinator.data.results.get(ATTR_VIN),
            ATTR_MODEL_YEAR: self.coordinator.data.results.get(ATTR_MODEL_YEAR),
            ATTR_FUEL_TYPE: self.coordinator.data.results.get(ATTR_FUEL_TYPE),
            ATTR_MATCH_SCORE: self.coordinator.data.results.get(ATTR_MATCH_SCORE),
            ATTR_CHARGING_SCHEDULE: self.coordinator.data.results.get(ATTR_CHARGING_SCHEDULE, []),
            ATTR_RAW_TWO_DAYS: self.coordinator.data.results.get(ATTR_RAW_TWO_DAYS, []),
            ATTR_PLAN_MODE: self.coordinator.data.results.get(ATTR_PLAN_MODE),
            ATTR_CHARGER_CONTROL_ENABLED: self.coordinator.data.results.get(
                ATTR_CHARGER_CONTROL_ENABLED
            ),
            ATTR_CHARGER_ENTITY: self.coordinator.data.results.get(ATTR_CHARGER_ENTITY),
            ATTR_CHARGER_STATUS_ENTITY: self.coordinator.data.results.get(
                ATTR_CHARGER_STATUS_ENTITY
            ),
            ATTR_CHARGER_BACKEND: self.coordinator.data.results.get(ATTR_CHARGER_BACKEND),
            ATTR_CHARGER_COMMANDABLE: self.coordinator.data.results.get(
                ATTR_CHARGER_COMMANDABLE
            ),
            ATTR_CHARGER_EXPECTED_ON: self.coordinator.data.results.get(
                ATTR_CHARGER_EXPECTED_ON
            ),
            ATTR_CHARGER_MISMATCH: self.coordinator.data.results.get(ATTR_CHARGER_MISMATCH),
            ATTR_LAST_CHARGER_COMMAND_AT: self.coordinator.data.results.get(
                ATTR_LAST_CHARGER_COMMAND_AT
            ),
            ATTR_LAST_CHARGER_COMMAND_REASON: self.coordinator.data.results.get(
                ATTR_LAST_CHARGER_COMMAND_REASON
            ),
            ATTR_CONTROL_TICK_INTERVAL: self.coordinator.data.results.get(
                ATTR_CONTROL_TICK_INTERVAL
            ),
            ATTR_DUMMY_CHARGER: self.coordinator.data.results.get(ATTR_DUMMY_CHARGER),
        }

    @property
    def native_value(self):
        return self.coordinator.data.results.get(self.entity_description.result_key)
