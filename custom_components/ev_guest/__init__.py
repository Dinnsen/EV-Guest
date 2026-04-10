"""The EV Guest integration."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, PLATFORMS, SERVICE_CALCULATE, SERVICE_GRAB_CAR_DATA
from .coordinator import EVGuestCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_SCHEMA = vol.Schema({vol.Required("entry_id"): cv.string})


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up EV Guest services."""

    async def _handle_grab(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call.data["entry_id"])
        await coordinator.async_lookup_car_data()

    async def _handle_calculate(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call.data["entry_id"])
        await coordinator.async_calculate()

    if not hass.services.has_service(DOMAIN, SERVICE_GRAB_CAR_DATA):
        hass.services.async_register(DOMAIN, SERVICE_GRAB_CAR_DATA, _handle_grab, schema=SERVICE_SCHEMA)
    if not hass.services.has_service(DOMAIN, SERVICE_CALCULATE):
        hass.services.async_register(DOMAIN, SERVICE_CALCULATE, _handle_calculate, schema=SERVICE_SCHEMA)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = EVGuestCoordinator(hass, entry)
    await coordinator.async_initialize()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: EVGuestCoordinator = entry.runtime_data
        await coordinator.async_shutdown()
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    _LOGGER.debug("Removing EV Guest entry %s", entry.entry_id)


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if entry.version < 3:
        entry.version = 3
    return True


def _get_coordinator(hass: HomeAssistant, entry_id: str) -> EVGuestCoordinator:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.entry_id == entry_id:
            return entry.runtime_data
    raise HomeAssistantError(f"Unknown EV Guest entry_id: {entry_id}")
