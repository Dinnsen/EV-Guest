"""The EV Guest integration."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_CHARGER_BACKEND,
    CONF_CHARGER_START_DATA,
    CONF_CHARGER_START_SERVICE,
    CONF_CHARGER_STATUS_ENTITY,
    CONF_CHARGER_STOP_DATA,
    CONF_CHARGER_STOP_SERVICE,
    CONF_CHARGER_SWITCH_ENTITY,
    CONF_COUNTRY,
    CONF_CURRENCY,
    CONF_DURATION_FORMAT,
    CONF_LANGUAGE,
    CONF_MOTORAPI_KEY,
    CONF_PRICE_ENTITY,
    CONF_TIME_FORMAT,
    COUNTRY_DK,
    DOMAIN,
    LANGUAGE_EN,
    PLATFORMS,
    SERVICE_CALCULATE,
    SERVICE_FORCE_START_CHARGER,
    SERVICE_FORCE_STOP_CHARGER,
    SERVICE_GRAB_CAR_DATA,
    SERVICE_RESYNC_CHARGER_PLAN,
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

    async def _handle_force_start(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call.data["entry_id"])
        await coordinator.async_force_start_charger()

    async def _handle_force_stop(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call.data["entry_id"])
        await coordinator.async_force_stop_charger()

    async def _handle_resync(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call.data["entry_id"])
        await coordinator.async_resync_charger_plan()

    if not hass.services.has_service(DOMAIN, SERVICE_GRAB_CAR_DATA):
        hass.services.async_register(
            DOMAIN, SERVICE_GRAB_CAR_DATA, _handle_grab, schema=SERVICE_SCHEMA
        )
    if not hass.services.has_service(DOMAIN, SERVICE_CALCULATE):
        hass.services.async_register(
            DOMAIN, SERVICE_CALCULATE, _handle_calculate, schema=SERVICE_SCHEMA
        )
    if not hass.services.has_service(DOMAIN, SERVICE_FORCE_START_CHARGER):
        hass.services.async_register(
            DOMAIN,
            SERVICE_FORCE_START_CHARGER,
            _handle_force_start,
            schema=SERVICE_SCHEMA,
        )
    if not hass.services.has_service(DOMAIN, SERVICE_FORCE_STOP_CHARGER):
        hass.services.async_register(
            DOMAIN,
            SERVICE_FORCE_STOP_CHARGER,
            _handle_force_stop,
            schema=SERVICE_SCHEMA,
        )
    if not hass.services.has_service(DOMAIN, SERVICE_RESYNC_CHARGER_PLAN):
        hass.services.async_register(
            DOMAIN,
            SERVICE_RESYNC_CHARGER_PLAN,
            _handle_resync,
            schema=SERVICE_SCHEMA,
        )
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
    if entry.version >= 7:
        return True

    new_data = dict(entry.data)
    new_data.setdefault("name", entry.title or "EV Guest")
    new_data.setdefault(CONF_PRICE_ENTITY, "sensor.energi_data_service")
    new_data.setdefault(CONF_CURRENCY, "DKK")
    new_data.setdefault(CONF_TIME_FORMAT, "24h")
    new_data.setdefault(CONF_DURATION_FORMAT, "minutes")
    new_data.setdefault(CONF_MOTORAPI_KEY, "")
    new_data.setdefault(CONF_CHARGER_SWITCH_ENTITY, "")
    new_data.setdefault(CONF_CHARGER_BACKEND, "generic_switch")
    new_data.setdefault(CONF_CHARGER_STATUS_ENTITY, new_data.get(CONF_CHARGER_SWITCH_ENTITY, ""))
    new_data.setdefault(CONF_CHARGER_START_SERVICE, "")
    new_data.setdefault(CONF_CHARGER_STOP_SERVICE, "")
    new_data.setdefault(CONF_CHARGER_START_DATA, "")
    new_data.setdefault(CONF_CHARGER_STOP_DATA, "")
    new_data.setdefault(CONF_LANGUAGE, LANGUAGE_EN)
    new_data.setdefault(CONF_COUNTRY, COUNTRY_DK)

    hass.config_entries.async_update_entry(entry, data=new_data, version=7, minor_version=0)
    _LOGGER.info("Migrated EV Guest config entry %s to version 7.0", entry.entry_id)
    return True


def _get_coordinator(hass: HomeAssistant, entry_id: str) -> EVGuestCoordinator:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.entry_id == entry_id and getattr(entry, "runtime_data", None) is not None:
            return entry.runtime_data
    raise HomeAssistantError(f"Unknown EV Guest entry_id: {entry_id}")
