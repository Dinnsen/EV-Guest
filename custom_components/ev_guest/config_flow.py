"""Config flow for EV Guest."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client, selector

from .api import EVGuestAuthError, EVGuestLookupError, async_validate_plate_provider_credentials
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
    COUNTRIES,
    CURRENCIES,
    DEFAULT_COUNTRY,
    DEFAULT_NAME,
    DEFAULT_PLATE_PROVIDER,
    DOMAIN,
    DURATION_FORMATS,
    TIME_FORMATS,
)


def _price_entity_selector() -> selector.EntitySelector:
    return selector.EntitySelector(
        selector.EntitySelectorConfig(
            filter=selector.EntityFilterSelectorConfig(domain=["sensor"])
        )
    )


def _charger_switch_entity_selector() -> selector.EntitySelector:
    return selector.EntitySelector(
        selector.EntitySelectorConfig(
            filter=selector.EntityFilterSelectorConfig(domain=["switch"]),
            multiple=False,
        )
    )


def _charger_status_entity_selector() -> selector.EntitySelector:
    return selector.EntitySelector(
        selector.EntitySelectorConfig(
            filter=selector.EntityFilterSelectorConfig(
                domain=["binary_sensor", "switch", "input_boolean"]
            ),
            multiple=False,
        )
    )


def _normalize_country(value: str | None) -> str:
    if not value:
        return DEFAULT_COUNTRY

    lowered = value.strip().lower()
    if lowered in {"dk", "denmark", "danmark"}:
        return "Denmark"

    return DEFAULT_COUNTRY if value not in COUNTRIES else value


def _normalize_optional_entity(value: Any) -> str:
    if not value:
        return ""

    entity_id = str(value).strip()
    if not entity_id or entity_id.lower() == "none":
        return ""

    if "ev_guest_dummy" in entity_id:
        return ""

    return entity_id


def _sanitize_optional_entity_default(
    hass: HomeAssistant,
    value: Any,
    *,
    allowed_domains: set[str],
) -> str | None:
    entity_id = _normalize_optional_entity(value)
    if not entity_id:
        return None

    if "." not in entity_id:
        return None

    domain = entity_id.split(".", 1)[0]
    if domain not in allowed_domains:
        return None

    if hass.states.get(entity_id) is None:
        return None

    return entity_id


def _user_schema(hass: HomeAssistant, defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required("name", default=defaults.get("name", DEFAULT_NAME)): str,
            vol.Required(
                CONF_PRICE_ENTITY,
                default=defaults.get(CONF_PRICE_ENTITY, "sensor.energi_data_service"),
            ): _price_entity_selector(),
            vol.Required(
                CONF_CURRENCY,
                default=defaults.get(CONF_CURRENCY, "DKK"),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=CURRENCIES,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_TIME_FORMAT,
                default=defaults.get(CONF_TIME_FORMAT, "24h"),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=TIME_FORMATS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_DURATION_FORMAT,
                default=defaults.get(CONF_DURATION_FORMAT, "minutes"),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=DURATION_FORMATS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_COUNTRY,
                default=_normalize_country(defaults.get(CONF_COUNTRY)),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=COUNTRIES,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_MOTORAPI_KEY,
                default=defaults.get(CONF_MOTORAPI_KEY, ""),
            ): str,
            vol.Optional(
                CONF_CHARGER_SWITCH_ENTITY,
                default=_sanitize_optional_entity_default(
                    hass,
                    defaults.get(CONF_CHARGER_SWITCH_ENTITY),
                    allowed_domains={"switch"},
                ),
            ): _charger_switch_entity_selector(),
            vol.Optional(
                CONF_CHARGER_STATUS_ENTITY,
                default=_sanitize_optional_entity_default(
                    hass,
                    defaults.get(CONF_CHARGER_STATUS_ENTITY),
                    allowed_domains={"binary_sensor", "switch", "input_boolean"},
                ),
            ): _charger_status_entity_selector(),
        }
    )


def _options_schema(hass: HomeAssistant, defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_PRICE_ENTITY,
                default=defaults.get(CONF_PRICE_ENTITY, "sensor.energi_data_service"),
            ): _price_entity_selector(),
            vol.Required(
                CONF_CURRENCY,
                default=defaults.get(CONF_CURRENCY, "DKK"),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=CURRENCIES,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_TIME_FORMAT,
                default=defaults.get(CONF_TIME_FORMAT, "24h"),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=TIME_FORMATS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_DURATION_FORMAT,
                default=defaults.get(CONF_DURATION_FORMAT, "minutes"),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=DURATION_FORMATS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_COUNTRY,
                default=_normalize_country(defaults.get(CONF_COUNTRY)),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=COUNTRIES,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(
                CONF_MOTORAPI_KEY,
                default=defaults.get(CONF_MOTORAPI_KEY, ""),
            ): str,
            vol.Optional(
                CONF_CHARGER_SWITCH_ENTITY,
                default=_sanitize_optional_entity_default(
                    hass,
                    defaults.get(CONF_CHARGER_SWITCH_ENTITY),
                    allowed_domains={"switch"},
                ),
            ): _charger_switch_entity_selector(),
            vol.Optional(
                CONF_CHARGER_STATUS_ENTITY,
                default=_sanitize_optional_entity_default(
                    hass,
                    defaults.get(CONF_CHARGER_STATUS_ENTITY),
                    allowed_domains={"binary_sensor", "switch", "input_boolean"},
                ),
            ): _charger_status_entity_selector(),
        }
    )


async def _validate_api_key(hass, country: str, api_key: str, provider: str | None = None) -> None:
    session = aiohttp_client.async_get_clientsession(hass)
    await async_validate_plate_provider_credentials(
        session,
        country=country,
        provider=provider or DEFAULT_PLATE_PROVIDER,
        api_key=api_key,
    )


class EVGuestConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 7
    MINOR_VERSION = 0

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        defaults: dict[str, Any] = {}
        if user_input is not None:
            defaults = user_input
            try:
                await _validate_api_key(
                    self.hass,
                    _normalize_country(user_input[CONF_COUNTRY]),
                    user_input[CONF_MOTORAPI_KEY],
                    DEFAULT_PLATE_PROVIDER,
                )
            except EVGuestAuthError:
                errors["base"] = "invalid_auth"
            except EVGuestLookupError as err:
                errors["base"] = str(err)
            else:
                entry_data = dict(user_input)
                entry_data[CONF_COUNTRY] = _normalize_country(user_input.get(CONF_COUNTRY))
                entry_data[CONF_CHARGER_SWITCH_ENTITY] = _normalize_optional_entity(
                    user_input.get(CONF_CHARGER_SWITCH_ENTITY)
                )
                entry_data[CONF_CHARGER_STATUS_ENTITY] = _normalize_optional_entity(
                    user_input.get(CONF_CHARGER_STATUS_ENTITY)
                )
                entry_data[CONF_PLATE_PROVIDER] = DEFAULT_PLATE_PROVIDER
                await self.async_set_unique_id(user_input["name"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=user_input["name"], data=entry_data)

        return self.async_show_form(
            step_id="user",
            data_schema=_user_schema(self.hass, defaults),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]):
        self._reauth_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            assert self._reauth_entry is not None
            current = {**self._reauth_entry.data, **self._reauth_entry.options}
            try:
                await _validate_api_key(
                    self.hass,
                    _normalize_country(current.get(CONF_COUNTRY, DEFAULT_COUNTRY)),
                    user_input[CONF_MOTORAPI_KEY],
                    current.get(CONF_PLATE_PROVIDER, DEFAULT_PLATE_PROVIDER),
                )
            except EVGuestAuthError:
                errors["base"] = "invalid_auth"
            except EVGuestLookupError as err:
                errors["base"] = str(err)
            else:
                self.hass.config_entries.async_update_entry(
                    self._reauth_entry,
                    data={**self._reauth_entry.data, CONF_MOTORAPI_KEY: user_input[CONF_MOTORAPI_KEY]},
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
            merged = dict(user_input)
            merged[CONF_COUNTRY] = _normalize_country(user_input.get(CONF_COUNTRY))
            merged[CONF_CHARGER_SWITCH_ENTITY] = _normalize_optional_entity(
                user_input.get(CONF_CHARGER_SWITCH_ENTITY)
            )
            merged[CONF_CHARGER_STATUS_ENTITY] = _normalize_optional_entity(
                user_input.get(CONF_CHARGER_STATUS_ENTITY)
            )
            merged[CONF_PLATE_PROVIDER] = current.get(CONF_PLATE_PROVIDER, DEFAULT_PLATE_PROVIDER)
            api_key = (merged.get(CONF_MOTORAPI_KEY) or "").strip()
            if not api_key:
                merged[CONF_MOTORAPI_KEY] = current.get(CONF_MOTORAPI_KEY, "")
                return self.async_create_entry(data=merged)
            try:
                await _validate_api_key(
                    self.hass,
                    merged.get(CONF_COUNTRY, DEFAULT_COUNTRY),
                    api_key,
                    merged.get(CONF_PLATE_PROVIDER, DEFAULT_PLATE_PROVIDER),
                )
            except EVGuestAuthError:
                errors["base"] = "invalid_auth"
            except EVGuestLookupError as err:
                errors["base"] = str(err)
            else:
                merged[CONF_MOTORAPI_KEY] = api_key
                return self.async_create_entry(data=merged)

        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(self.hass, current),
            errors=errors,
        )
