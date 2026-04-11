"""The EV Guest integration."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_CHARGER_SWITCH_ENTITY,
    DOMAIN,
    PLATFORMS,
    SERVICE_CALCULATE,
    SERVICE_GRAB_CAR_DATA,
)
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
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: EVGuestCoordinator = entry.runtime_data
        await coordinator.async_shutdown()
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    _LOGGER.debug("Removing EV Guest entry %s", entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate older EV Guest config entries to the latest format."""
    if entry.version >= 5:
        return True

    new_data = dict(entry.data)
    new_data.setdefault("name", entry.title or "EV Guest")
    new_data.setdefault("price_entity", "sensor.energi_data_service")
    new_data.setdefault("currency", "DKK")
    new_data.setdefault("time_format", "24h")
    new_data.setdefault("duration_format", "minutes")
    new_data.setdefault("motorapi_api_key", "")
    new_data.setdefault(CONF_CHARGER_SWITCH_ENTITY, "")

    hass.config_entries.async_update_entry(entry, data=new_data, version=5, minor_version=0)
    _LOGGER.info("Migrated EV Guest config entry %s to version 5.0", entry.entry_id)
    return True


def _get_coordinator(hass: HomeAssistant, entry_id: str) -> EVGuestCoordinator:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.entry_id == entry_id and getattr(entry, "runtime_data", None) is not None:
            return entry.runtime_data
    raise HomeAssistantError(f"Unknown EV Guest entry_id: {entry_id}")
