"""HTTP tests for the MotorAPI, NHTSA and Open EV Data helpers."""

from __future__ import annotations

from aiohttp import ClientError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import pytest
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.ev_guest import api
from custom_components.ev_guest.const import (
    MOTORAPI_BASE_URL,
    NHTSA_DECODE_URL,
    OPEN_EV_DATA_FALLBACK_URL,
    OPEN_EV_DATA_URL,
)

DATASET = [
    {"brand": "Tesla", "model": "Model 3", "variant": "Long Range", "battery_capacity": 75, "model_year": 2023},
    {"brand": "Fiat", "model": "500e", "battery_capacity": 37.3},
]


@pytest.mark.parametrize(
    ("status", "error"),
    [(200, None), (404, None), (401, api.EVGuestAuthError), (500, api.EVGuestLookupError)],
)
async def test_validate_key(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, status: int, error: type[Exception] | None
) -> None:
    aioclient_mock.get(f"{MOTORAPI_BASE_URL}/vehicles/AA00000", status=status)
    session = async_get_clientsession(hass)

    if error is None:
        await api.async_validate_plate_provider_credentials(session, "Denmark", None, "key")
    else:
        with pytest.raises(error):
            await api.async_validate_plate_provider_credentials(session, "Denmark", None, "key")


@pytest.mark.parametrize(("exc", "reason"), [(ClientError(), "cannot_connect"), (TimeoutError(), "timeout")])
async def test_validate_key_connection_errors(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, exc: Exception, reason: str
) -> None:
    aioclient_mock.get(f"{MOTORAPI_BASE_URL}/vehicles/AA00000", exc=exc)

    with pytest.raises(api.EVGuestLookupError, match=reason):
        await api.async_validate_motorapi_key(async_get_clientsession(hass), "key")


async def test_validate_requires_key_and_known_provider(hass: HomeAssistant) -> None:
    session = async_get_clientsession(hass)
    with pytest.raises(api.EVGuestAuthError):
        await api.async_validate_motorapi_key(session, "")
    with pytest.raises(api.EVGuestLookupError, match="unsupported_provider"):
        await api.async_validate_plate_provider_credentials(session, "Denmark", "other", "key")
    with pytest.raises(api.EVGuestLookupError, match="unsupported_provider"):
        await api.async_lookup_vehicle(session, "AB12345", "key", "Denmark", "other")


async def test_lookup_vehicle(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.get(
        f"{MOTORAPI_BASE_URL}/vehicles/AB12345",
        json={"vin": "VIN1", "make": "Tesla", "model": "Model 3", "version": "LR", "model_year": "2023"},
    )

    result = await api.async_lookup_vehicle(async_get_clientsession(hass), "ab 12-345", "key", "Denmark")

    assert (result.plate, result.vin, result.brand, result.variant, result.model_year) == (
        "AB12345",
        "VIN1",
        "Tesla",
        "LR",
        2023,
    )


@pytest.mark.parametrize(
    ("kwargs", "error", "reason"),
    [
        ({"status": 401}, api.EVGuestAuthError, "invalid_auth"),
        ({"status": 404}, api.EVGuestLookupError, "vehicle_not_found"),
        ({"status": 503}, api.EVGuestLookupError, "unexpected_http_503"),
        ({"exc": ClientError()}, api.EVGuestLookupError, "cannot_connect"),
        ({"exc": TimeoutError()}, api.EVGuestLookupError, "timeout"),
    ],
)
async def test_lookup_vehicle_errors(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, kwargs: dict, error: type[Exception], reason: str
) -> None:
    aioclient_mock.get(f"{MOTORAPI_BASE_URL}/vehicles/AB12345", **kwargs)

    with pytest.raises(error, match=reason):
        await api.async_lookup_vehicle_motorapi(async_get_clientsession(hass), "AB12345", "key")


async def test_lookup_vehicle_needs_plate_and_key(hass: HomeAssistant) -> None:
    session = async_get_clientsession(hass)
    with pytest.raises(api.EVGuestLookupError, match="empty_plate"):
        await api.async_lookup_vehicle_motorapi(session, " - ", "key")
    with pytest.raises(api.EVGuestAuthError):
        await api.async_lookup_vehicle_motorapi(session, "AB12345", "")


async def test_decode_vin(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    url = NHTSA_DECODE_URL.format(vin="VIN1") + "&modelyear=2023"
    aioclient_mock.get(url, json={"Results": [{"Make": "TESLA", "Model": "Model 3", "Trim": "Long Range"}]})

    result = await api.async_decode_vin_nhtsa(async_get_clientsession(hass), "vin1", 2023)

    assert result is not None
    assert (result.brand, result.variant, result.model_year) == ("TESLA", "Long Range", 2023)


@pytest.mark.parametrize(
    "kwargs",
    [{"status": 500}, {"exc": ClientError()}, {"json": {"Results": []}}, {"json": {"Results": ["x"]}}, {"json": []}],
)
async def test_decode_vin_returns_none_on_problems(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, kwargs: dict
) -> None:
    aioclient_mock.get(NHTSA_DECODE_URL.format(vin="VIN1"), **kwargs)

    assert await api.async_decode_vin_nhtsa(async_get_clientsession(hass), "VIN1") is None


async def test_decode_empty_vin(hass: HomeAssistant) -> None:
    assert await api.async_decode_vin_nhtsa(async_get_clientsession(hass), "--") is None


async def test_battery_lookup_matches_and_falls_back(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.get(OPEN_EV_DATA_URL, status=404)
    aioclient_mock.get(OPEN_EV_DATA_FALLBACK_URL, json=DATASET)
    session = async_get_clientsession(hass)

    match = await api.async_lookup_battery_open_ev_data(session, "Tesla", "Model 3", "Long Range", 2023)
    assert match.battery_capacity == 75
    assert match.match_score is not None

    weak = await api.async_lookup_battery_open_ev_data(session, "Volvo", "EX30", None, None)
    assert weak.battery_capacity is None


async def test_battery_lookup_without_dataset(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.get(OPEN_EV_DATA_URL, exc=ClientError())
    aioclient_mock.get(OPEN_EV_DATA_FALLBACK_URL, exc=TimeoutError())

    result = await api.async_lookup_battery_open_ev_data(async_get_clientsession(hass), "Tesla", "Model 3", None, None)

    assert result == api.BatteryLookupResult(None, "Open EV Data", None, None)


def test_provider_registry_helpers() -> None:
    assert api.get_default_plate_provider(None) == "motorapi_dk"
    assert "motorapi_dk" in api.get_supported_plate_providers(None)
    assert api.get_supported_plate_providers("Sweden") == {}
    assert api._extract_year("x") is None
