"""The EV Guest integration."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_CHARGER_STATUS_ENTITY,
    CONF_CHARGER_SWITCH_ENTITY,
    CONF_COUNTRY,
    CONF_CURRENCY,
    CONF_DURATION_FORMAT,
    CONF_MOTORAPI_KEY,
    CONF_PLATE_PROVIDER,
    CONF_PRICE_ENTITY,
    CONF_TIME_FORMAT,
    DEFAULT_COUNTRY,
    DEFAULT_PLATE_PROVIDER,
    DOMAIN,
    PLATFORMS,
    SERVICE_CALCULATE,
    SERVICE_GRAB_CAR_DATA,
)
from .coordinator import EVGuestCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_SCHEMA = vol.Schema({vol.Required("entry_id"): cv.string})


def _normalize_country(value: str | None) -> str:
    if not value:
        return DEFAULT_COUNTRY

    lowered = value.strip().lower()
    if lowered in {"dk", "denmark", "danmark"}:
        return "Denmark"

    return DEFAULT_COUNTRY


def _normalize_optional_entity(value: str | None) -> str:
    if not value:
        return ""

    entity_id = str(value).strip()
    if not entity_id or entity_id.lower() == "none":
        return ""

    if "ev_guest_dummy" in entity_id:
        return ""

    return entity_id


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
    current_data = dict(entry.data)
    current_options = dict(entry.options)

    new_data = dict(current_data)
    new_options = dict(current_options)

    new_data.setdefault("name", entry.title or "EV Guest")
    new_data.setdefault(CONF_PRICE_ENTITY, "sensor.energi_data_service")
    new_data.setdefault(CONF_CURRENCY, "DKK")
    new_data.setdefault(CONF_TIME_FORMAT, "24h")
    new_data.setdefault(CONF_DURATION_FORMAT, "minutes")
    new_data.setdefault(CONF_MOTORAPI_KEY, "")
    new_data.setdefault(CONF_PLATE_PROVIDER, DEFAULT_PLATE_PROVIDER)
    new_data[CONF_COUNTRY] = _normalize_country(new_data.get(CONF_COUNTRY))
    new_data[CONF_CHARGER_SWITCH_ENTITY] = _normalize_optional_entity(
        new_data.get(CONF_CHARGER_SWITCH_ENTITY)
    )
    new_data[CONF_CHARGER_STATUS_ENTITY] = _normalize_optional_entity(
        new_data.get(CONF_CHARGER_STATUS_ENTITY)
    )
    new_data.pop("language", None)

    if CONF_COUNTRY in new_options:
        new_options[CONF_COUNTRY] = _normalize_country(new_options.get(CONF_COUNTRY))
    if CONF_CHARGER_SWITCH_ENTITY in new_options:
        new_options[CONF_CHARGER_SWITCH_ENTITY] = _normalize_optional_entity(
            new_options.get(CONF_CHARGER_SWITCH_ENTITY)
        )
    if CONF_CHARGER_STATUS_ENTITY in new_options:
        new_options[CONF_CHARGER_STATUS_ENTITY] = _normalize_optional_entity(
            new_options.get(CONF_CHARGER_STATUS_ENTITY)
        )
    new_options.pop("language", None)

    changed = (
        entry.version < 7
        or entry.minor_version != 0
        or new_data != current_data
        or new_options != current_options
    )
    if not changed:
        return True

    hass.config_entries.async_update_entry(entry, data=new_data, options=new_options, version=7, minor_version=0)
    _LOGGER.info("Migrated EV Guest config entry %s to version 7.0", entry.entry_id)
    return True


def _get_coordinator(hass: HomeAssistant, entry_id: str) -> EVGuestCoordinator:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.entry_id == entry_id and getattr(entry, "runtime_data", None) is not None:
            return entry.runtime_data
    raise HomeAssistantError(f"Unknown EV Guest entry_id: {entry_id}")
