"""Config flow for EV Guest."""

from __future__ import annotations

from json import JSONDecodeError, loads as json_loads
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import aiohttp_client, selector

from .api import (
    EVGuestAuthError,
    EVGuestLookupError,
    async_validate_country_provider_credentials,
)
from .const import (
    BACKENDS_REQUIRING_SWITCH,
    CHARGER_BACKENDS,
    CHARGER_BACKEND_DUMMY,
    CHARGER_BACKEND_GENERIC,
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
    COUNTRIES,
    CURRENCIES,
    DEFAULT_NAME,
    DOMAIN,
    DURATION_FORMATS,
    LANGUAGES,
    TIME_FORMATS,
)


def _price_entity_selector() -> selector.EntitySelector:
    return selector.EntitySelector(
        selector.EntitySelectorConfig(
            filter=selector.EntityFilterSelectorConfig(domain=["sensor"])
        )
    )


def _charger_entity_selector() -> selector.EntitySelector:
    return selector.EntitySelector(
        selector.EntitySelectorConfig(
            filter=selector.EntityFilterSelectorConfig(domain=["switch"])
        )
    )


def _charger_status_entity_selector() -> selector.EntitySelector:
    return selector.EntitySelector(
        selector.EntitySelectorConfig(
            filter=selector.EntityFilterSelectorConfig(
                domain=["switch", "binary_sensor", "input_boolean"]
            )
        )
    )


def _select(options: list[str], translation_key: str) -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=options,
            mode=selector.SelectSelectorMode.DROPDOWN,
            translation_key=translation_key,
        )
    )


def _common_schema(defaults: dict[str, Any], *, include_name: bool) -> dict:
    schema: dict = {}
    if include_name:
        schema[vol.Required("name", default=defaults.get("name", DEFAULT_NAME))] = str
    schema.update(
        {
            vol.Required(CONF_LANGUAGE, default=defaults.get(CONF_LANGUAGE, "en")): _select(LANGUAGES, "language"),
            vol.Required(CONF_COUNTRY, default=defaults.get(CONF_COUNTRY, "dk")): _select(COUNTRIES, "country"),
            vol.Required(
                CONF_PRICE_ENTITY,
                default=defaults.get(CONF_PRICE_ENTITY, "sensor.energi_data_service"),
            ): _price_entity_selector(),
            vol.Required(CONF_CURRENCY, default=defaults.get(CONF_CURRENCY, "DKK")): _select(CURRENCIES, "currency"),
            vol.Required(CONF_TIME_FORMAT, default=defaults.get(CONF_TIME_FORMAT, "24h")): _select(TIME_FORMATS, "time_format"),
            vol.Required(
                CONF_DURATION_FORMAT,
                default=defaults.get(CONF_DURATION_FORMAT, "minutes"),
            ): _select(DURATION_FORMATS, "duration_format"),
            vol.Required(CONF_MOTORAPI_KEY, default=defaults.get(CONF_MOTORAPI_KEY, "")): str,
            vol.Required(
                CONF_CHARGER_BACKEND,
                default=defaults.get(CONF_CHARGER_BACKEND, CHARGER_BACKEND_GENERIC),
            ): _select(CHARGER_BACKENDS, "charger_backend"),
            vol.Optional(
                CONF_CHARGER_SWITCH_ENTITY,
                default=defaults.get(CONF_CHARGER_SWITCH_ENTITY, ""),
            ): _charger_entity_selector(),
            vol.Optional(
                CONF_CHARGER_STATUS_ENTITY,
                default=defaults.get(CONF_CHARGER_STATUS_ENTITY, defaults.get(CONF_CHARGER_SWITCH_ENTITY, "")),
            ): _charger_status_entity_selector(),
            vol.Optional(
                CONF_CHARGER_START_SERVICE,
                default=defaults.get(CONF_CHARGER_START_SERVICE, ""),
            ): str,
            vol.Optional(
                CONF_CHARGER_STOP_SERVICE,
                default=defaults.get(CONF_CHARGER_STOP_SERVICE, ""),
            ): str,
            vol.Optional(
                CONF_CHARGER_START_DATA,
                default=defaults.get(CONF_CHARGER_START_DATA, ""),
            ): str,
            vol.Optional(
                CONF_CHARGER_STOP_DATA,
                default=defaults.get(CONF_CHARGER_STOP_DATA, ""),
            ): str,
        }
    )
    return schema


def _normalize_payload(data: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(data)
    for key in (
        CONF_MOTORAPI_KEY,
        CONF_CHARGER_SWITCH_ENTITY,
        CONF_CHARGER_STATUS_ENTITY,
        CONF_CHARGER_START_SERVICE,
        CONF_CHARGER_STOP_SERVICE,
        CONF_CHARGER_START_DATA,
        CONF_CHARGER_STOP_DATA,
    ):
        value = normalized.get(key)
        if isinstance(value, str):
            normalized[key] = value.strip()

    backend = normalized.get(CONF_CHARGER_BACKEND, CHARGER_BACKEND_GENERIC)
    if backend == CHARGER_BACKEND_DUMMY:
        normalized[CONF_CHARGER_SWITCH_ENTITY] = ""
        normalized[CONF_CHARGER_STATUS_ENTITY] = normalized.get(CONF_CHARGER_STATUS_ENTITY, "")
        normalized.setdefault(CONF_CHARGER_START_SERVICE, "")
        normalized.setdefault(CONF_CHARGER_STOP_SERVICE, "")
    elif not normalized.get(CONF_CHARGER_STATUS_ENTITY) and normalized.get(CONF_CHARGER_SWITCH_ENTITY):
        normalized[CONF_CHARGER_STATUS_ENTITY] = normalized[CONF_CHARGER_SWITCH_ENTITY]

    return normalized


def _validate_json_blob(value: str, field_name: str) -> None:
    if not value:
        return
    try:
        parsed = json_loads(value)
    except JSONDecodeError as err:
        raise EVGuestLookupError(f"invalid_{field_name}") from err
    if not isinstance(parsed, dict):
        raise EVGuestLookupError(f"invalid_{field_name}")


async def _validate_user_input(hass, user_input: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_payload(user_input)
    _validate_json_blob(normalized.get(CONF_CHARGER_START_DATA, ""), CONF_CHARGER_START_DATA)
    _validate_json_blob(normalized.get(CONF_CHARGER_STOP_DATA, ""), CONF_CHARGER_STOP_DATA)

    backend = normalized.get(CONF_CHARGER_BACKEND, CHARGER_BACKEND_GENERIC)
    switch_entity = normalized.get(CONF_CHARGER_SWITCH_ENTITY, "")
    start_service = normalized.get(CONF_CHARGER_START_SERVICE, "")
    stop_service = normalized.get(CONF_CHARGER_STOP_SERVICE, "")

    if backend in BACKENDS_REQUIRING_SWITCH and not switch_entity:
        raise EVGuestLookupError("charger_entity_required")
    if backend == "ha_ev_smart_charging" and not (switch_entity or (start_service and stop_service)):
        raise EVGuestLookupError("smart_charging_mapping_required")

    session = aiohttp_client.async_get_clientsession(hass)
    await async_validate_country_provider_credentials(
        session,
        normalized[CONF_COUNTRY],
        normalized[CONF_MOTORAPI_KEY],
    )
    return normalized


def _user_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(_common_schema(defaults, include_name=True))


def _options_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(_common_schema(defaults, include_name=False))


class EVGuestConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 7
    MINOR_VERSION = 0

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        defaults: dict[str, Any] = {}
        if user_input is not None:
            defaults = user_input
            try:
                normalized = await _validate_user_input(self.hass, user_input)
            except EVGuestAuthError:
                errors["base"] = "invalid_auth"
            except EVGuestLookupError as err:
                errors["base"] = str(err)
            else:
                await self.async_set_unique_id(normalized["name"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=normalized["name"], data=normalized)
        return self.async_show_form(step_id="user", data_schema=_user_schema(defaults), errors=errors)

    async def async_step_reauth(self, entry_data: dict[str, Any]):
        self._reauth_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                current = {**self._reauth_entry.data, **self._reauth_entry.options}
                merged = {**current, CONF_MOTORAPI_KEY: user_input[CONF_MOTORAPI_KEY]}
                await _validate_user_input(self.hass, merged)
            except EVGuestAuthError:
                errors["base"] = "invalid_auth"
            except EVGuestLookupError as err:
                errors["base"] = str(err)
            else:
                assert self._reauth_entry is not None
                self.hass.config_entries.async_update_entry(
                    self._reauth_entry,
                    data={**self._reauth_entry.data, CONF_MOTORAPI_KEY: user_input[CONF_MOTORAPI_KEY].strip()},
                )
                await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_MOTORAPI_KEY): str}),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry):
        return EVGuestOptionsFlow(config_entry)


class EVGuestOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        current = {**self._config_entry.data, **self._config_entry.options}
        if user_input is not None:
            merged = {**current, **user_input}
            try:
                validated = await _validate_user_input(self.hass, merged)
            except EVGuestAuthError:
                errors["base"] = "invalid_auth"
            except EVGuestLookupError as err:
                errors["base"] = str(err)
            else:
                payload = dict(validated)
                payload.pop("name", None)
                return self.async_create_entry(data=payload)
        return self.async_show_form(step_id="init", data_schema=_options_schema(current), errors=errors)
