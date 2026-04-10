from unittest.mock import AsyncMock, patch

from custom_components.ev_guest.const import CONF_MOTORAPI_KEY, CONF_PRICE_ENTITY


async def test_user_flow_success(hass):
    result = await hass.config_entries.flow.async_init("ev_guest", context={"source": "user"})
    assert result["type"] == "form"

    with patch("custom_components.ev_guest.config_flow.async_validate_motorapi_key", AsyncMock(return_value=None)):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "name": "EV Guest",
                CONF_PRICE_ENTITY: "sensor.energi_data_service",
                "currency": "DKK",
                "time_format": "24h",
                "duration_format": "minutes",
                CONF_MOTORAPI_KEY: "test-key",
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
            CONF_PRICE_ENTITY: "sensor.energi_data_service",
            "currency": "DKK",
            "time_format": "24h",
            "duration_format": "minutes",
            CONF_MOTORAPI_KEY: "",
        },
    )
    assert result2["type"] == "create_entry"
    assert result2["data"][CONF_MOTORAPI_KEY] == mock_config_entry.data[CONF_MOTORAPI_KEY]
