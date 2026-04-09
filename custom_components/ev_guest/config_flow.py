"""Config flow for EV Guest."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from aiohttp import ClientSession
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


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required("name", default=defaults.get("name", DEFAULT_NAME)): str,
            vol.Required(CONF_PRICE_ENTITY, default=defaults.get(CONF_PRICE_ENTITY)): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(CONF_CURRENCY, default=defaults.get(CONF_CURRENCY, "DKK")): selector.SelectSelector(
                selector.SelectSelectorConfig(options=CURRENCIES, mode=selector.SelectSelectorMode.DROPDOWN)
            ),
            vol.Required(CONF_TIME_FORMAT, default=defaults.get(CONF_TIME_FORMAT, "24h")): selector.SelectSelector(
                selector.SelectSelectorConfig(options=TIME_FORMATS, mode=selector.SelectSelectorMode.DROPDOWN)
            ),
            vol.Required(
                CONF_DURATION_FORMAT,
                default=defaults.get(CONF_DURATION_FORMAT, "minutes"),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(options=DURATION_FORMATS, mode=selector.SelectSelectorMode.DROPDOWN)
            ),
            vol.Required(CONF_MOTORAPI_KEY, default=defaults.get(CONF_MOTORAPI_KEY, "")): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
            ),
        }
    )


async def _validate_input(session: ClientSession, data: dict[str, Any]) -> None:
    await async_validate_motorapi_key(session, data[CONF_MOTORAPI_KEY])


class EVGuestConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            session = aiohttp_client.async_get_clientsession(self.hass)
            try:
                await _validate_input(session, user_input)
            except EVGuestAuthError:
                errors["base"] = "invalid_auth"
            except EVGuestLookupError as err:
                errors["base"] = str(err)
            else:
                await self.async_set_unique_id(user_input["name"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=user_input["name"], data=user_input)

        return self.async_show_form(step_id="user", data_schema=_schema({}), errors=errors)

    async def async_step_reauth(self, entry_data: dict[str, Any]):
        self._reauth_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            session = aiohttp_client.async_get_clientsession(self.hass)
            try:
                await async_validate_motorapi_key(session, user_input[CONF_MOTORAPI_KEY])
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
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MOTORAPI_KEY): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                    )
                }
            ),
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
            session = aiohttp_client.async_get_clientsession(self.hass)
            try:
                await _validate_input(session, {**current, **user_input})
            except EVGuestAuthError:
                errors["base"] = "invalid_auth"
            except EVGuestLookupError as err:
                errors["base"] = str(err)
            else:
                user_input.pop("name", None)
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=_schema(current), errors=errors)
