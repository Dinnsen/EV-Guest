"""Config flow for EV Guest."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import aiohttp_client, selector

from .api import EVGuestAuthError, EVGuestLookupError, async_validate_motorapi_key
from .const import (
    CONF_CURRENCY,
    CONF_DURATION_FORMAT,
    CONF_MOTORAPI_KEY,
    CONF_PRICE_ENTITY,
    CONF_TIME_FORMAT,
    CURRENCIES,
    DEFAULT_NAME,
    DOMAIN,
    DURATION_FORMATS,
    TIME_FORMATS,
)


def _entity_selector() -> selector.EntitySelector:
    return selector.EntitySelector(
        selector.EntitySelectorConfig(
            filter=selector.EntityFilterSelectorConfig(domain=["sensor"])
        )
    )


def _user_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required("name", default=defaults.get("name", DEFAULT_NAME)): str,
            vol.Required(CONF_PRICE_ENTITY, default=defaults.get(CONF_PRICE_ENTITY, "sensor.energi_data_service")): _entity_selector(),
            vol.Required(CONF_CURRENCY, default=defaults.get(CONF_CURRENCY, "DKK")): selector.SelectSelector(
                selector.SelectSelectorConfig(options=CURRENCIES, mode=selector.SelectSelectorMode.DROPDOWN)
            ),
            vol.Required(CONF_TIME_FORMAT, default=defaults.get(CONF_TIME_FORMAT, "24h")): selector.SelectSelector(
                selector.SelectSelectorConfig(options=TIME_FORMATS, mode=selector.SelectSelectorMode.DROPDOWN)
            ),
            vol.Required(CONF_DURATION_FORMAT, default=defaults.get(CONF_DURATION_FORMAT, "minutes")): selector.SelectSelector(
                selector.SelectSelectorConfig(options=DURATION_FORMATS, mode=selector.SelectSelectorMode.DROPDOWN)
            ),
            vol.Required(CONF_MOTORAPI_KEY, default=defaults.get(CONF_MOTORAPI_KEY, "")): str,
        }
    )


def _options_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_PRICE_ENTITY, default=defaults.get(CONF_PRICE_ENTITY, "sensor.energi_data_service")): _entity_selector(),
            vol.Required(CONF_CURRENCY, default=defaults.get(CONF_CURRENCY, "DKK")): selector.SelectSelector(
                selector.SelectSelectorConfig(options=CURRENCIES, mode=selector.SelectSelectorMode.DROPDOWN)
            ),
            vol.Required(CONF_TIME_FORMAT, default=defaults.get(CONF_TIME_FORMAT, "24h")): selector.SelectSelector(
                selector.SelectSelectorConfig(options=TIME_FORMATS, mode=selector.SelectSelectorMode.DROPDOWN)
            ),
            vol.Required(CONF_DURATION_FORMAT, default=defaults.get(CONF_DURATION_FORMAT, "minutes")): selector.SelectSelector(
                selector.SelectSelectorConfig(options=DURATION_FORMATS, mode=selector.SelectSelectorMode.DROPDOWN)
            ),
            vol.Required(CONF_MOTORAPI_KEY, default=defaults.get(CONF_MOTORAPI_KEY, "")): str,
        }
    )


async def _validate_api_key(hass, api_key: str) -> None:
    session = aiohttp_client.async_get_clientsession(hass)
    await async_validate_motorapi_key(session, api_key)


class EVGuestConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 4
    MINOR_VERSION = 0

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        defaults: dict[str, Any] = {}
        if user_input is not None:
            defaults = user_input
            try:
                await _validate_api_key(self.hass, user_input[CONF_MOTORAPI_KEY])
            except EVGuestAuthError:
                errors["base"] = "invalid_auth"
            except EVGuestLookupError as err:
                errors["base"] = str(err)
            else:
                await self.async_set_unique_id(user_input["name"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=user_input["name"], data=user_input)

        return self.async_show_form(step_id="user", data_schema=_user_schema(defaults), errors=errors)

    async def async_step_reauth(self, entry_data: dict[str, Any]):
        self._reauth_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await _validate_api_key(self.hass, user_input[CONF_MOTORAPI_KEY])
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
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        current = {**self.config_entry.data, **self.config_entry.options}
        if user_input is not None:
            merged = dict(user_input)
            api_key = (merged.get(CONF_MOTORAPI_KEY) or "").strip()
            if not api_key:
                merged[CONF_MOTORAPI_KEY] = current.get(CONF_MOTORAPI_KEY, "")
                return self.async_create_entry(data=merged)
            try:
                await _validate_api_key(self.hass, api_key)
            except EVGuestAuthError:
                errors["base"] = "invalid_auth"
            except EVGuestLookupError as err:
                errors["base"] = str(err)
            else:
                merged[CONF_MOTORAPI_KEY] = api_key
                return self.async_create_entry(data=merged)

        return self.async_show_form(step_id="init", data_schema=_options_schema(current), errors=errors)
