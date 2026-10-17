"""Binary sensor platform for EV Guest."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DIAGNOSTIC_BEHIND_PLAN, DIAGNOSTIC_CHARGE_NOW
from .coordinator import EVGuestConfigEntry, EVGuestCoordinator
from .entity import EVGuestEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EVGuestConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = [EVGuestChargeNowBinarySensor(coordinator)]
    if coordinator.energy_entity:
        entities.append(EVGuestBehindPlanBinarySensor(coordinator))
    async_add_entities(entities)


class EVGuestChargeNowBinarySensor(EVGuestEntity, BinarySensorEntity):
    """On exactly while the current time is inside a planned charging segment."""

    def __init__(self, coordinator: EVGuestCoordinator) -> None:
        super().__init__(coordinator, DIAGNOSTIC_CHARGE_NOW)

    @property
    def is_on(self) -> bool:
        return self.coordinator.is_charge_now()


class EVGuestBehindPlanBinarySensor(EVGuestEntity, BinarySensorEntity):
    """On when the energy meter has counted clearly less than the plan expects.

    Only created with an energy meter. Unknown without a plan.
    """

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator: EVGuestCoordinator) -> None:
        super().__init__(coordinator, DIAGNOSTIC_BEHIND_PLAN)

    @property
    def is_on(self) -> bool | None:
        progress = self.coordinator.progress()
        return None if progress is None else progress.behind_plan
