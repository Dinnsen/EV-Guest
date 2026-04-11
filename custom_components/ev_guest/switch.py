"""Switch platform for EV Guest."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    INPUT_CONTINUOUS_CHARGING_PREFERRED,
    INPUT_ENABLE_CHARGER_CONTROL,
    INPUT_USE_COMPLETION_TIME,
)
from .entity import EVGuestCoordinatorEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [
            EVGuestUseCompletionTimeSwitch(coordinator),
            EVGuestEnableChargerControlSwitch(coordinator),
            EVGuestContinuousChargingPreferredSwitch(coordinator),
            EVGuestDummyTestChargerSwitch(coordinator),
        ]
    )


class _BaseInputSwitch(EVGuestCoordinatorEntity, SwitchEntity):
    _default = False

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.inputs.get(self._key, self._default))

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_input_value(self._key, True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_input_value(self._key, False)


class EVGuestUseCompletionTimeSwitch(_BaseInputSwitch):
    """Toggle whether completion time should be enforced."""

    _attr_name = "Use Charge Completion Time"
    _attr_icon = "mdi:clock-check-outline"
    _default = True

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, INPUT_USE_COMPLETION_TIME)


class EVGuestEnableChargerControlSwitch(_BaseInputSwitch):
    """Toggle charger control on or off."""

    _attr_name = "Enable Charger Control"
    _attr_icon = "mdi:ev-station"
    _default = False

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, INPUT_ENABLE_CHARGER_CONTROL)


class EVGuestContinuousChargingPreferredSwitch(_BaseInputSwitch):
    """Prefer one continuous charging block."""

    _attr_name = "Continuous Charging Preferred"
    _attr_icon = "mdi:timeline-clock-outline"
    _default = True

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, INPUT_CONTINUOUS_CHARGING_PREFERRED)


class EVGuestDummyTestChargerSwitch(EVGuestCoordinatorEntity, SwitchEntity):
    """Internal dummy charger for integration testing."""

    _attr_name = "Dummy Test Charger"
    _attr_icon = "mdi:ev-station"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "dummy_test_charger")

    @property
    def available(self) -> bool:
        return self.coordinator.uses_dummy_backend

    @property
    def is_on(self) -> bool:
        return self.coordinator.dummy_charger_on

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_dummy_charger_state(True, reason="manual_dummy_switch")

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_dummy_charger_state(False, reason="manual_dummy_switch")
