"""Config flow for EV Guest."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlowWithReload
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util
import voluptuous as vol

from .api import EVGuestAuthError, EVGuestLookupError, async_validate_plate_provider_credentials
from .const import (
    CONF_COUNTRY,
    CONF_CURRENCY,
    CONF_MOTORAPI_KEY,
    CONF_PLATE_PROVIDER,
    CONF_PRICE_ENTITY,
    CONNECTION_KEYS,
    COUNTRIES,
    CURRENCIES,
    DEFAULT_COUNTRY,
    DEFAULT_CURRENCY,
    DEFAULT_NAME,
    DEFAULT_PLATE_PROVIDER,
    DEFAULT_PRICE_ENTITY,
    DOMAIN,
)
from .prices import extract_price_slots

PRICE_ENTITY_SELECTOR = selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor"))
COUNTRY_SELECTOR = selector.SelectSelector(
    selector.SelectSelectorConfig(options=COUNTRIES, mode=selector.SelectSelectorMode.DROPDOWN)
)
API_KEY_SELECTOR = selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD))


def _currency_selector(hass: HomeAssistant) -> selector.SelectSelector:
    options = list(CURRENCIES)
    if hass.config.currency and hass.config.currency not in options:
        options.append(hass.config.currency)
    return selector.SelectSelector(
        selector.SelectSelectorConfig(options=options, mode=selector.SelectSelectorMode.DROPDOWN)
    )


def _default_currency(hass: HomeAssistant) -> str:
    return hass.config.currency or DEFAULT_CURRENCY


def _connection_schema(defaults: Mapping[str, Any]) -> dict[vol.Marker, Any]:
    return {
        vol.Required(CONF_PRICE_ENTITY, default=defaults.get(CONF_PRICE_ENTITY, DEFAULT_PRICE_ENTITY)): (
            PRICE_ENTITY_SELECTOR
        ),
        vol.Required(CONF_COUNTRY, default=defaults.get(CONF_COUNTRY, DEFAULT_COUNTRY)): COUNTRY_SELECTOR,
        vol.Optional(CONF_MOTORAPI_KEY, default=defaults.get(CONF_MOTORAPI_KEY, "")): API_KEY_SELECTOR,
    }


async def _async_validate_connection(hass: HomeAssistant, user_input: Mapping[str, Any]) -> dict[str, str]:
    """Check the price sensor and, if given, the MotorAPI key."""
    errors: dict[str, str] = {}
    price_state = hass.states.get(user_input[CONF_PRICE_ENTITY])
    if not extract_price_slots(price_state, dt_util.now()):
        errors[CONF_PRICE_ENTITY] = "invalid_price_entity"

    api_key = str(user_input.get(CONF_MOTORAPI_KEY) or "").strip()
    if api_key:
        try:
            await async_validate_plate_provider_credentials(
                async_get_clientsession(hass),
                country=user_input.get(CONF_COUNTRY, DEFAULT_COUNTRY),
                provider=DEFAULT_PLATE_PROVIDER,
                api_key=api_key,
            )
        except EVGuestAuthError:
            errors[CONF_MOTORAPI_KEY] = "invalid_auth"
        except EVGuestLookupError as err:
            errors["base"] = (
                str(err) if str(err) in {"cannot_connect", "timeout", "unsupported_provider"} else "unknown"
            )
    return errors


class EVGuestConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for EV Guest."""

    VERSION = 7
    MINOR_VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_NAME])
            self._abort_if_unique_id_configured()
            errors = await _async_validate_connection(self.hass, user_input)
            if not errors:
                data = {
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_PRICE_ENTITY: user_input[CONF_PRICE_ENTITY],
                    CONF_COUNTRY: user_input[CONF_COUNTRY],
                    CONF_MOTORAPI_KEY: str(user_input.get(CONF_MOTORAPI_KEY) or "").strip(),
                    CONF_PLATE_PROVIDER: DEFAULT_PLATE_PROVIDER,
                }
                options = {CONF_CURRENCY: user_input[CONF_CURRENCY]}
                return self.async_create_entry(title=user_input[CONF_NAME], data=data, options=options)

        defaults = user_input or {}
        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): str,
                **_connection_schema(defaults),
                vol.Required(CONF_CURRENCY, default=defaults.get(CONF_CURRENCY, _default_currency(self.hass))): (
                    _currency_selector(self.hass)
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Change the price sensor, country or MotorAPI key."""
        entry = self._get_reconfigure_entry()
        current = {**entry.data, **entry.options}
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = await _async_validate_connection(self.hass, user_input)
            if not errors:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_PRICE_ENTITY: user_input[CONF_PRICE_ENTITY],
                        CONF_COUNTRY: user_input[CONF_COUNTRY],
                        CONF_MOTORAPI_KEY: str(user_input.get(CONF_MOTORAPI_KEY) or "").strip(),
                    },
                    options={k: v for k, v in entry.options.items() if k not in CONNECTION_KEYS},
                )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(_connection_schema(user_input or current)),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Enter a new MotorAPI key."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            api_key = str(user_input[CONF_MOTORAPI_KEY]).strip()
            try:
                await async_validate_plate_provider_credentials(
                    async_get_clientsession(self.hass),
                    country=entry.data.get(CONF_COUNTRY, DEFAULT_COUNTRY),
                    provider=entry.data.get(CONF_PLATE_PROVIDER, DEFAULT_PLATE_PROVIDER),
                    api_key=api_key,
                )
            except EVGuestAuthError:
                errors[CONF_MOTORAPI_KEY] = "invalid_auth"
            except EVGuestLookupError as err:
                errors["base"] = str(err) if str(err) in {"cannot_connect", "timeout"} else "unknown"
            else:
                return self.async_update_reload_and_abort(entry, data_updates={CONF_MOTORAPI_KEY: api_key})

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_MOTORAPI_KEY): API_KEY_SELECTOR}),
            description_placeholders={"name": entry.title},
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> EVGuestOptionsFlow:
        return EVGuestOptionsFlow()


class EVGuestOptionsFlow(OptionsFlowWithReload):
    """Preferences; changes reload the entry automatically."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = self.config_entry.options.get(CONF_CURRENCY) or self.config_entry.data.get(CONF_CURRENCY)
        schema = vol.Schema(
            {
                vol.Required(CONF_CURRENCY, default=current or _default_currency(self.hass)): _currency_selector(
                    self.hass
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
