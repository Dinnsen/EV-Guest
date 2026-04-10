from __future__ import annotations

from unittest.mock import patch

from custom_components.ev_guest.const import (
    CONF_CURRENCY,
    CONF_DURATION_FORMAT,
    CONF_ELECTRICITY_PRICE_SENSOR,
    CONF_MOTORAPI_API_KEY,
    CONF_TIME_FORMAT,
)


async def test_user_flow_success(hass):
    result = await hass.config_entries.flow.async_init(
        "ev_guest", context={"source": "user"}
    )
    assert result["type"] == "form"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ELECTRICITY_PRICE_SENSOR: "sensor.energi_data_service",
            CONF_CURRENCY: "DKK",
            CONF_TIME_FORMAT: "24h",
            CONF_DURATION_FORMAT: "minutes",
            CONF_MOTORAPI_API_KEY: "test-key",
        },
    )
    assert result2["type"] == "create_entry"


async def test_options_flow_blank_key_keeps_existing(hass, mock_config_entry):
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] == "form"

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_ELECTRICITY_PRICE_SENSOR: "sensor.energi_data_service",
            CONF_CURRENCY: "DKK",
            CONF_TIME_FORMAT: "24h",
            CONF_DURATION_FORMAT: "minutes",
            CONF_MOTORAPI_API_KEY: "",
        },
    )
    assert result2["type"] == "create_entry"
    assert (
        result2["data"][CONF_MOTORAPI_API_KEY]
        == mock_config_entry.data[CONF_MOTORAPI_API_KEY]
    )


async def test_options_flow_init_does_not_crash_on_config_entry_property(
    hass, mock_config_entry
):
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] == "form"