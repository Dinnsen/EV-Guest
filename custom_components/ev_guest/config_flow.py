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
    DOMAIN,
    DURATION_FORMATS,
    TIME_FORMATS,
)


def _entity_selector() -> selector.EntitySelector:
    """Return entity selector for price sensor."""
    return selector.EntitySelector(
        selector.EntitySelectorConfig(
            domain="sensor",
        )
    )


def _build_schema(current: dict[str, Any]) -> vol.Schema:
    """Build config/options schema."""
    return vol.Schema(
        {
            vol.Required(
                CONF_PRICE_ENTITY,
                default=current.get(CONF_PRICE_ENTITY, ""),
            ): _entity_selector(),
            vol.Required(
                CONF_CURRENCY,
                default=current.get(CONF_CURRENCY, "DKK"),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=CURRENCIES,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_TIME_FORMAT,
                default=current.get(CONF_TIME_FORMAT, "24h"),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=TIME_FORMATS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_DURATION_FORMAT,
                default=current.get(CONF_DURATION_FORMAT, "minutes"),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=DURATION_FORMATS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(
                CONF_MOTORAPI_KEY,
                default=current.get(CONF_MOTORAPI_KEY, ""),
            ): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.TEXT,
                    autocomplete="off",
                )
            ),
        }
    )


class EVGuestConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for EV Guest."""

    VERSION = 4

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            data = dict(user_input)

            if not data.get(CONF_MOTORAPI_KEY):
                errors[CONF_MOTORAPI_KEY] = "required"
            else:
                return self.async_create_entry(title="EV Guest", data=data)

        schema = _build_schema({})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return EVGuestOptionsFlow(config_entry)


class EVGuestOptionsFlow(config_entries.OptionsFlow):
    """Handle EV Guest options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}

        current: dict[str, Any] = {
            **self._config_entry.data,
            **self._config_entry.options,
        }

        if user_input is not None:
            new_options = dict(user_input)

            # Keep existing API key if left blank in Configure
            if not new_options.get(CONF_MOTORAPI_KEY):
                existing_key = current.get(CONF_MOTORAPI_KEY, "")
                if existing_key:
                    new_options[CONF_MOTORAPI_KEY] = existing_key
                else:
                    errors[CONF_MOTORAPI_KEY] = "required"

            if not errors:
                return self.async_create_entry(title="", data=new_options)

        schema = _build_schema(current)
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
