"""Config flow for EV Guest."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import aiohttp_client, selector

from . import const as c

# Optional API helpers. The v0.6.0 package may contain the new provider-layer
# helpers, but older layouts should still work with the simple MotorAPI helper.
from .api import EVGuestAuthError, EVGuestLookupError

try:  # v0.6.0 style
    from .api import async_validate_plate_provider_credentials
except ImportError:  # pragma: no cover - fallback for older layouts
    async_validate_plate_provider_credentials = None

try:  # v0.4.0 / v0.5.1 style
    from .api import async_validate_motorapi_key
except ImportError:  # pragma: no cover
    async_validate_motorapi_key = None


DOMAIN = c.DOMAIN
DEFAULT_NAME = c.DEFAULT_NAME

CONF_PRICE_ENTITY = c.CONF_PRICE_ENTITY
CONF_CURRENCY = c.CONF_CURRENCY
CONF_TIME_FORMAT = c.CONF_TIME_FORMAT
CONF_DURATION_FORMAT = c.CONF_DURATION_FORMAT
CONF_MOTORAPI_KEY = c.CONF_MOTORAPI_KEY
CONF_CHARGER_SWITCH_ENTITY = c.CONF_CHARGER_SWITCH_ENTITY
CONF_CHARGER_STATUS_ENTITY = getattr(c, "CONF_CHARGER_STATUS_ENTITY", "charger_status_entity")
CONF_LANGUAGE = getattr(c, "CONF_LANGUAGE", "language")
CONF_COUNTRY = getattr(c, "CONF_COUNTRY", "country")
CONF_PLATE_PROVIDER = getattr(c, "CONF_PLATE_PROVIDER", "plate_provider")

CURRENCIES = c.CURRENCIES
TIME_FORMATS = c.TIME_FORMATS
DURATION_FORMATS = c.DURATION_FORMATS

LANGUAGE_OPTIONS = ["en", "da"]
COUNTRY_OPTIONS = ["DK"]


def _select(options: list[str], default: str) -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=options,
            mode=selector.SelectSelectorMode.DROPDOWN,
            translation_key=default if False else None,
        )
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


def _charger_status_selector() -> selector.EntitySelector:
    return selector.EntitySelector(
        selector.EntitySelectorConfig(
            filter=selector.EntityFilterSelectorConfig(domain=["switch", "binary_sensor", "sensor"])
        )
    )


def _optional_entity_field(
    key: str,
    default_value: str | None,
    entity_selector: selector.EntitySelector,
) -> tuple[vol.Marker, selector.EntitySelector]:
    """Return an optional selector field without using vol.Any('', selector).

    voluptuous_serialize cannot convert vol.Any('', selector.EntitySelector(...)),
    which causes the 500 error in the config flow UI.
    """
    if default_value:
        return vol.Optional(key, default=default_value), entity_selector
    return vol.Optional(key), entity_selector


def _clean_optional_entity(value: str | None) -> str | None:
    if not value:
        return None
    return value


async def _validate_provider(hass, data: dict[str, Any]) -> None:
    """Validate credentials/provider settings."""
    api_key = (data.get(CONF_MOTORAPI_KEY) or "").strip()
    country = data.get(CONF_COUNTRY, "DK")
    provider = data.get(CONF_PLATE_PROVIDER)
    session = aiohttp_client.async_get_clientsession(hass)

    if async_validate_plate_provider_credentials is not None:
        await async_validate_plate_provider_credentials(
            session,
            country=country,
            provider=provider,
            api_key=api_key,
        )
        return

    if async_validate_motorapi_key is not None:
        await async_validate_motorapi_key(session, api_key)
        return

    raise EVGuestLookupError("missing_validator")


def _user_schema(defaults: dict[str, Any]) -> vol.Schema:
    charger_switch_key, charger_switch_selector = _optional_entity_field(
        CONF_CHARGER_SWITCH_ENTITY,
        defaults.get(CONF_CHARGER_SWITCH_ENTITY),
        _charger_entity_selector(),
    )
    charger_status_key, charger_status_selector = _optional_entity_field(
        CONF_CHARGER_STATUS_ENTITY,
        defaults.get(CONF_CHARGER_STATUS_ENTITY),
        _charger_status_selector(),
    )

    schema: dict[Any, Any] = {
        vol.Required("name", default=defaults.get("name", DEFAULT_NAME)): str,
        vol.Required(
            CONF_PRICE_ENTITY,
            default=defaults.get(CONF_PRICE_ENTITY, "sensor.energi_data_service"),
        ): _price_entity_selector(),
        vol.Required(
            CONF_CURRENCY,
            default=defaults.get(CONF_CURRENCY, "DKK"),
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(options=CURRENCIES, mode=selector.SelectSelectorMode.DROPDOWN)
        ),
        vol.Required(
            CONF_TIME_FORMAT,
            default=defaults.get(CONF_TIME_FORMAT, "24h"),
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(options=TIME_FORMATS, mode=selector.SelectSelectorMode.DROPDOWN)
        ),
        vol.Required(
            CONF_DURATION_FORMAT,
            default=defaults.get(CONF_DURATION_FORMAT, "minutes"),
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(options=DURATION_FORMATS, mode=selector.SelectSelectorMode.DROPDOWN)
        ),
    }

    if CONF_LANGUAGE:
        schema[vol.Required(CONF_LANGUAGE, default=defaults.get(CONF_LANGUAGE, "en"))] = selector.SelectSelector(
            selector.SelectSelectorConfig(options=LANGUAGE_OPTIONS, mode=selector.SelectSelectorMode.DROPDOWN)
        )
    if CONF_COUNTRY:
        schema[vol.Required(CONF_COUNTRY, default=defaults.get(CONF_COUNTRY, "DK"))] = selector.SelectSelector(
            selector.SelectSelectorConfig(options=COUNTRY_OPTIONS, mode=selector.SelectSelectorMode.DROPDOWN)
        )
    if CONF_PLATE_PROVIDER:
        schema[vol.Optional(CONF_PLATE_PROVIDER, default=defaults.get(CONF_PLATE_PROVIDER, "motorapi"))] = str

    schema[vol.Required(CONF_MOTORAPI_KEY, default=defaults.get(CONF_MOTORAPI_KEY, ""))] = str
    schema[charger_switch_key] = charger_switch_selector
    schema[charger_status_key] = charger_status_selector

    return vol.Schema(schema)


def _options_schema(defaults: dict[str, Any]) -> vol.Schema:
    charger_switch_key, charger_switch_selector = _optional_entity_field(
        CONF_CHARGER_SWITCH_ENTITY,
        defaults.get(CONF_CHARGER_SWITCH_ENTITY),
        _charger_entity_selector(),
    )
    charger_status_key, charger_status_selector = _optional_entity_field(
        CONF_CHARGER_STATUS_ENTITY,
        defaults.get(CONF_CHARGER_STATUS_ENTITY),
        _charger_status_selector(),
    )

    schema: dict[Any, Any] = {
        vol.Required(
            CONF_PRICE_ENTITY,
            default=defaults.get(CONF_PRICE_ENTITY, "sensor.energi_data_service"),
        ): _price_entity_selector(),
        vol.Required(
            CONF_CURRENCY,
            default=defaults.get(CONF_CURRENCY, "DKK"),
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(options=CURRENCIES, mode=selector.SelectSelectorMode.DROPDOWN)
        ),
        vol.Required(
            CONF_TIME_FORMAT,
            default=defaults.get(CONF_TIME_FORMAT, "24h"),
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(options=TIME_FORMATS, mode=selector.SelectSelectorMode.DROPDOWN)
        ),
        vol.Required(
            CONF_DURATION_FORMAT,
            default=defaults.get(CONF_DURATION_FORMAT, "minutes"),
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(options=DURATION_FORMATS, mode=selector.SelectSelectorMode.DROPDOWN)
        ),
    }

    if CONF_LANGUAGE:
        schema[vol.Required(CONF_LANGUAGE, default=defaults.get(CONF_LANGUAGE, "en"))] = selector.SelectSelector(
            selector.SelectSelectorConfig(options=LANGUAGE_OPTIONS, mode=selector.SelectSelectorMode.DROPDOWN)
        )
    if CONF_COUNTRY:
        schema[vol.Required(CONF_COUNTRY, default=defaults.get(CONF_COUNTRY, "DK"))] = selector.SelectSelector(
            selector.SelectSelectorConfig(options=COUNTRY_OPTIONS, mode=selector.SelectSelectorMode.DROPDOWN)
        )
    if CONF_PLATE_PROVIDER:
        schema[vol.Optional(CONF_PLATE_PROVIDER, default=defaults.get(CONF_PLATE_PROVIDER, "motorapi"))] = str

    schema[vol.Optional(CONF_MOTORAPI_KEY, default=defaults.get(CONF_MOTORAPI_KEY, ""))] = str
    schema[charger_switch_key] = charger_switch_selector
    schema[charger_status_key] = charger_status_selector

    return vol.Schema(schema)


class EVGuestConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 6
    MINOR_VERSION = 0

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        defaults: dict[str, Any] = {}
        if user_input is not None:
            defaults = user_input
            cleaned = dict(user_input)
            cleaned[CONF_CHARGER_SWITCH_ENTITY] = _clean_optional_entity(cleaned.get(CONF_CHARGER_SWITCH_ENTITY))
            cleaned[CONF_CHARGER_STATUS_ENTITY] = _clean_optional_entity(cleaned.get(CONF_CHARGER_STATUS_ENTITY))
            try:
                await _validate_provider(self.hass, cleaned)
            except EVGuestAuthError:
                errors["base"] = "invalid_auth"
            except EVGuestLookupError as err:
                errors["base"] = str(err)
            else:
                await self.async_set_unique_id(cleaned["name"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=cleaned["name"], data=cleaned)

        return self.async_show_form(step_id="user", data_schema=_user_schema(defaults), errors=errors)

    async def async_step_reauth(self, entry_data: dict[str, Any]):
        self._reauth_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            current = dict(self._reauth_entry.data) if self._reauth_entry else {}
            current[CONF_MOTORAPI_KEY] = user_input[CONF_MOTORAPI_KEY]
            try:
                await _validate_provider(self.hass, current)
            except EVGuestAuthError:
                errors["base"] = "invalid_auth"
            except EVGuestLookupError as err:
                errors["base"] = str(err)
            else:
                assert self._reauth_entry is not None
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
            merged[CONF_CHARGER_SWITCH_ENTITY] = _clean_optional_entity(merged.get(CONF_CHARGER_SWITCH_ENTITY))
            merged[CONF_CHARGER_STATUS_ENTITY] = _clean_optional_entity(merged.get(CONF_CHARGER_STATUS_ENTITY))
            api_key = (merged.get(CONF_MOTORAPI_KEY) or "").strip()
            if not api_key:
                merged[CONF_MOTORAPI_KEY] = current.get(CONF_MOTORAPI_KEY, "")
                return self.async_create_entry(data=merged)
            try:
                await _validate_provider(self.hass, merged)
            except EVGuestAuthError:
                errors["base"] = "invalid_auth"
            except EVGuestLookupError as err:
                errors["base"] = str(err)
            else:
                merged[CONF_MOTORAPI_KEY] = api_key
                return self.async_create_entry(data=merged)

        return self.async_show_form(step_id="init", data_schema=_options_schema(current), errors=errors)
