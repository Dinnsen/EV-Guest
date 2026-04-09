"""Config flow for EV Guest."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

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


class EVGuestConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for EV Guest."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input["name"])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input["name"], data=user_input)

        schema = vol.Schema(
            {
                vol.Required("name", default=DEFAULT_NAME): str,
                vol.Required(CONF_PRICE_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(CONF_CURRENCY, default="DKK"): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=CURRENCIES, mode=selector.SelectSelectorMode.DROPDOWN)
                ),
                vol.Required(CONF_TIME_FORMAT, default="24h"): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=TIME_FORMATS, mode=selector.SelectSelectorMode.DROPDOWN)
                ),
                vol.Required(CONF_DURATION_FORMAT, default="minutes"): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=DURATION_FORMATS, mode=selector.SelectSelectorMode.DROPDOWN)
                ),
                vol.Required(CONF_MOTORAPI_KEY): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry):
        return EVGuestOptionsFlow(config_entry)


class EVGuestOptionsFlow(config_entries.OptionsFlow):
    """Options flow for EV Guest."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {**self.config_entry.data, **self.config_entry.options}
        schema = vol.Schema(
            {
                vol.Required(CONF_PRICE_ENTITY, default=current[CONF_PRICE_ENTITY]): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(CONF_CURRENCY, default=current[CONF_CURRENCY]): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=CURRENCIES, mode=selector.SelectSelectorMode.DROPDOWN)
                ),
                vol.Required(CONF_TIME_FORMAT, default=current[CONF_TIME_FORMAT]): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=TIME_FORMATS, mode=selector.SelectSelectorMode.DROPDOWN)
                ),
                vol.Required(
                    CONF_DURATION_FORMAT,
                    default=current[CONF_DURATION_FORMAT],
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=DURATION_FORMATS, mode=selector.SelectSelectorMode.DROPDOWN)
                ),
                vol.Required(CONF_MOTORAPI_KEY, default=current.get(CONF_MOTORAPI_KEY, "")): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
