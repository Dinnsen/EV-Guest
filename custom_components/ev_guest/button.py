"""Button platform for EV Guest."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
            EVGuestGrabCarDataButton(coordinator),
            EVGuestCalculateButton(coordinator),
            EVGuestForceStartChargerButton(coordinator),
            EVGuestForceStopChargerButton(coordinator),
            EVGuestResyncPlanButton(coordinator),
            EVGuestResetDummyChargerButton(coordinator),
        ]
    )


class _BaseActionButton(EVGuestCoordinatorEntity, ButtonEntity):
    _attr_has_entity_name = True

    async def async_press(self) -> None:
        raise NotImplementedError


class EVGuestGrabCarDataButton(_BaseActionButton):
    _attr_name = "Grab Car Data"
    _attr_icon = "mdi:car-search"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "grab_car_data_button")

    async def async_press(self) -> None:
        await self.coordinator.async_lookup_car_data()


class EVGuestCalculateButton(_BaseActionButton):
    _attr_name = "Calculate"
    _attr_icon = "mdi:calculator-variant-outline"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "calculate_button")

    async def async_press(self) -> None:
        await self.coordinator.async_calculate()


class EVGuestForceStartChargerButton(_BaseActionButton):
    _attr_name = "Force Start Charger"
    _attr_icon = "mdi:play-circle-outline"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "force_start_charger_button")

    async def async_press(self) -> None:
        await self.coordinator.async_force_start_charger()


class EVGuestForceStopChargerButton(_BaseActionButton):
    _attr_name = "Force Stop Charger"
    _attr_icon = "mdi:stop-circle-outline"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "force_stop_charger_button")

    async def async_press(self) -> None:
        await self.coordinator.async_force_stop_charger()


class EVGuestResyncPlanButton(_BaseActionButton):
    _attr_name = "Resync Charger Plan"
    _attr_icon = "mdi:sync-circle"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "resync_plan_button")

    async def async_press(self) -> None:
        await self.coordinator.async_resync_charger_plan()


class EVGuestResetDummyChargerButton(_BaseActionButton):
    _attr_name = "Reset Dummy Test Charger"
    _attr_icon = "mdi:test-tube"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "reset_dummy_charger_button")

    @property
    def available(self) -> bool:
        return self.coordinator.uses_dummy_backend

    async def async_press(self) -> None:
        await self.coordinator.async_reset_dummy_charger()
