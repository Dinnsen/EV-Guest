"""Entity helpers for EV Guest."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EVGuestCoordinator


class EVGuestCoordinatorEntity(CoordinatorEntity[EVGuestCoordinator], Entity):
    """Base entity class."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: EVGuestCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_translation_key = key
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=coordinator.config_entry.title,
            manufacturer="Dinnsen",
            model="EV Guest",
            configuration_url="https://github.com/Dinnsen/EV-Guest",
        )
