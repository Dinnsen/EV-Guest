"""The EV Guest integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_COUNTRY,
    CONF_CURRENCY,
    CONF_MOTORAPI_KEY,
    CONF_PLATE_PROVIDER,
    CONF_PRICE_ENTITY,
    CONNECTION_KEYS,
    DEFAULT_COUNTRY,
    DEFAULT_CURRENCY,
    DEFAULT_PLATE_PROVIDER,
    DEFAULT_PRICE_ENTITY,
    DOMAIN,
    LEGACY_ENTITIES,
    PLATFORMS,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .coordinator import EVGuestConfigEntry, EVGuestCoordinator
from .services import async_setup_services

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the EV Guest actions."""
    async_setup_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: EVGuestConfigEntry) -> bool:
    """Set up EV Guest from a config entry."""
    _remove_legacy_entities(hass, entry)
    coordinator = EVGuestCoordinator(hass, entry)
    await coordinator.async_initialize()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: EVGuestConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.async_shutdown()
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove stored inputs and plan when the entry is deleted."""
    store: Store[dict] = Store(hass, STORAGE_VERSION, STORAGE_KEY.format(entry_id=entry.entry_id))
    await store.async_remove()


def _remove_legacy_entities(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove entities replaced or removed in later versions."""
    registry = er.async_get(hass)
    for platform, key in LEGACY_ENTITIES:
        if entity_id := registry.async_get_entity_id(platform, DOMAIN, f"{entry.entry_id}_{key}"):
            registry.async_remove(entity_id)
            _LOGGER.info("Removed legacy entity %s", entity_id)


def _normalize_country(value: str | None) -> str:
    if value and value.strip().lower() in {"dk", "denmark", "danmark"}:
        return DEFAULT_COUNTRY
    return DEFAULT_COUNTRY


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate older config entries.

    Old keys (charger settings, time and duration formats) are left in place
    so that a downgrade still finds its configuration.
    """
    if entry.version > 7:
        return False

    data = dict(entry.data)
    options = dict(entry.options)

    if entry.version < 7:
        data.setdefault("name", entry.title or "EV Guest")
        data.setdefault(CONF_PRICE_ENTITY, DEFAULT_PRICE_ENTITY)
        data.setdefault(CONF_CURRENCY, DEFAULT_CURRENCY)
        data.setdefault(CONF_MOTORAPI_KEY, "")
        data.setdefault(CONF_PLATE_PROVIDER, DEFAULT_PLATE_PROVIDER)
        data[CONF_COUNTRY] = _normalize_country(data.get(CONF_COUNTRY))
        data.pop("language", None)
        options.pop("language", None)
        if CONF_COUNTRY in options:
            options[CONF_COUNTRY] = _normalize_country(options.get(CONF_COUNTRY))

    # 7.1: connection settings live in data (changed via reconfigure);
    # options only hold preferences.
    for key in CONNECTION_KEYS:
        if key in options:
            value = options.pop(key)
            if key != CONF_MOTORAPI_KEY or value:
                data[key] = value

    hass.config_entries.async_update_entry(entry, data=data, options=options, version=7, minor_version=1)
    _LOGGER.debug("Migrated EV Guest config entry %s to version 7.1", entry.entry_id)
    return True
