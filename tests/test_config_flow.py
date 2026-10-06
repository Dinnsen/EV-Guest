"""Tests for the EV Guest config, reconfigure, reauth and options flows."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ev_guest.api import EVGuestAuthError, EVGuestLookupError
from custom_components.ev_guest.const import DOMAIN

from .conftest import CONTINUOUS_PRICES, PRICE_ENTITY, set_prices

VALIDATE = "custom_components.ev_guest.config_flow.async_validate_plate_provider_credentials"
USER_INPUT = {
    "name": "Guest charger",
    "price_entity": PRICE_ENTITY,
    "country": "Denmark",
    "motorapi_api_key": "",
    "currency": "DKK",
}


@pytest.fixture(autouse=True)
def prices(hass: HomeAssistant, now: datetime) -> None:
    set_prices(hass, now, CONTINUOUS_PRICES)


@pytest.fixture(autouse=True)
def no_setup():
    """Do not set up the entry when a flow creates or reloads it."""
    with patch("custom_components.ev_guest.async_setup_entry", return_value=True) as mock:
        yield mock


async def test_user_flow_without_key(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Guest charger"
    assert result["data"] == {
        "name": "Guest charger",
        "price_entity": PRICE_ENTITY,
        "country": "Denmark",
        "motorapi_api_key": "",
        "plate_provider": "motorapi_dk",
    }
    assert result["options"] == {"currency": "DKK"}
    assert result["result"].minor_version == 1


async def test_user_flow_with_key(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    with patch(VALIDATE) as validate:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**USER_INPUT, "motorapi_api_key": " secret "}
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["motorapi_api_key"] == "secret"
    validate.assert_awaited_once()


@pytest.mark.parametrize(
    ("side_effect", "field", "error"),
    [
        (EVGuestAuthError("invalid_auth"), "motorapi_api_key", "invalid_auth"),
        (EVGuestLookupError("cannot_connect"), "base", "cannot_connect"),
        (EVGuestLookupError("unexpected_http_500"), "base", "unknown"),
    ],
)
async def test_user_flow_key_errors_then_recover(
    hass: HomeAssistant, side_effect: Exception, field: str, error: str
) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    with patch(VALIDATE, side_effect=side_effect):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**USER_INPUT, "motorapi_api_key": "bad"}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {field: error}

    with patch(VALIDATE):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**USER_INPUT, "motorapi_api_key": "good"}
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_user_flow_rejects_sensor_without_prices(hass: HomeAssistant) -> None:
    hass.states.async_set("sensor.temperature", "21")
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**USER_INPUT, "price_entity": "sensor.temperature"}
    )

    assert result["errors"] == {"price_entity": "invalid_price_entity"}


async def test_user_flow_aborts_on_duplicate_name(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {**USER_INPUT, "name": "EV Guest"})

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reconfigure(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    hass.states.async_set("sensor.nordpool", "1", {"raw_today": [{"hour": "2026-04-09T20:00:00+02:00", "price": 1.0}]})
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(mock_config_entry, options={"currency": "DKK", "price_entity": "sensor.old"})

    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["step_id"] == "reconfigure"

    with patch(VALIDATE):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"price_entity": "sensor.nordpool", "country": "Denmark", "motorapi_api_key": "new"},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data["price_entity"] == "sensor.nordpool"
    assert mock_config_entry.data["motorapi_api_key"] == "new"
    assert mock_config_entry.options == {"currency": "DKK"}


async def test_reconfigure_error(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"price_entity": "sensor.missing", "country": "Denmark", "motorapi_api_key": ""}
    )

    assert result["errors"] == {"price_entity": "invalid_price_entity"}


async def test_reauth(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"

    with patch(VALIDATE, side_effect=EVGuestAuthError("invalid_auth")):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {"motorapi_api_key": "bad"})
    assert result["errors"] == {"motorapi_api_key": "invalid_auth"}

    with patch(VALIDATE, side_effect=EVGuestLookupError("timeout")):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {"motorapi_api_key": "x"})
    assert result["errors"] == {"base": "timeout"}

    with patch(VALIDATE):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {"motorapi_api_key": " good "})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data["motorapi_api_key"] == "good"


async def test_options_flow(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(result["flow_id"], {"currency": "EUR"})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert mock_config_entry.options == {"currency": "EUR"}
