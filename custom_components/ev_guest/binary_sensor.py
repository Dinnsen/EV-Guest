"""Binary sensor platform for EV Guest."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import EVGuestCoordinatorEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [
            EVGuestPlannedActiveBinarySensor(coordinator),
            EVGuestExpectedOnBinarySensor(coordinator),
            EVGuestActualOnBinarySensor(coordinator),
            EVGuestMismatchBinarySensor(coordinator),
            EVGuestCommandableBinarySensor(coordinator),
        ]
    )


class _BaseDiagnosticBinarySensor(EVGuestCoordinatorEntity, BinarySensorEntity):
    _attr_entity_category = "diagnostic"


class EVGuestPlannedActiveBinarySensor(_BaseDiagnosticBinarySensor):
    _attr_name = "Charging Slot Active"
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "charging_slot_active")

    @property
    def is_on(self) -> bool:
        return self.coordinator.is_planned_active_now


class EVGuestExpectedOnBinarySensor(_BaseDiagnosticBinarySensor):
    _attr_name = "Charger Expected On"
    _attr_icon = "mdi:flash-outline"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "charger_expected_on")

    @property
    def is_on(self) -> bool:
        return self.coordinator.expected_charger_on


class EVGuestActualOnBinarySensor(_BaseDiagnosticBinarySensor):
    _attr_name = "Charger Actual On"
    _attr_icon = "mdi:ev-station"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "charger_actual_on")

    @property
    def available(self) -> bool:
        return self.coordinator.actual_charger_on is not None

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.actual_charger_on


class EVGuestMismatchBinarySensor(_BaseDiagnosticBinarySensor):
    _attr_name = "Charger State Mismatch"
    _attr_icon = "mdi:alert-outline"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "charger_state_mismatch")

    @property
    def available(self) -> bool:
        return self.coordinator.actual_charger_on is not None

    @property
    def is_on(self) -> bool:
        return self.coordinator.charger_state_mismatch


class EVGuestCommandableBinarySensor(_BaseDiagnosticBinarySensor):
    _attr_name = "Charger Commandable"
    _attr_icon = "mdi:remote"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "charger_commandable")

    @property
    def is_on(self) -> bool:
        return self.coordinator.is_charger_commandable
