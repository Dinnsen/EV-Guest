"""Fixtures for EV Guest tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence
from datetime import datetime, timedelta

from freezegun.api import FrozenDateTimeFactory
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ev_guest.const import (
    CONF_COUNTRY,
    CONF_CURRENCY,
    CONF_MOTORAPI_KEY,
    CONF_PLATE_PROVIDER,
    CONF_PRICE_ENTITY,
    DEFAULT_PLATE_PROVIDER,
    DOMAIN,
)

PRICE_ENTITY = "sensor.energi_data_service"
NOW = "2026-04-09T20:00:00+02:00"

# Prices from 20:00 used by the continuous example: the cheapest 4.2 h
# block before 07:00 starts at 22:00.
CONTINUOUS_PRICES = [1.80, 1.50, 0.40, 0.30, 0.20, 0.25, 0.90, 1.10, 1.30, 1.40, 1.60]
# Prices from 20:00 used by the split example.
SPLIT_PRICES = [1.80, 0.10, 1.50, 0.20, 1.40, 0.30, 1.30]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Allow loading custom_components in every test."""


@pytest.fixture
async def now(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> datetime:
    """Freeze time at 20:00 Copenhagen time."""
    await hass.config.async_set_time_zone("Europe/Copenhagen")
    moment = dt_util.parse_datetime(NOW)
    assert moment is not None
    freezer.move_to(moment)
    return moment


def set_prices(hass: HomeAssistant, start: datetime, prices: Sequence[float]) -> None:
    """Set the price sensor with hourly prices starting at ``start``."""
    hass.states.async_set(
        PRICE_ENTITY,
        str(prices[0]),
        {
            "raw_today": [
                {"hour": (start + timedelta(hours=offset)).isoformat(), "price": price}
                for offset, price in enumerate(prices)
            ],
            "raw_tomorrow": [],
        },
    )


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """An EV Guest entry without a MotorAPI key."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="EV Guest",
        unique_id="EV Guest",
        data={
            "name": "EV Guest",
            CONF_PRICE_ENTITY: PRICE_ENTITY,
            CONF_COUNTRY: "Denmark",
            CONF_MOTORAPI_KEY: "",
            CONF_PLATE_PROVIDER: DEFAULT_PLATE_PROVIDER,
        },
        options={CONF_CURRENCY: "DKK"},
        version=7,
        minor_version=1,
    )


@pytest.fixture
async def init_integration(
    hass: HomeAssistant, now: datetime, mock_config_entry: MockConfigEntry
) -> AsyncGenerator[MockConfigEntry]:
    """Set up EV Guest with the continuous example prices."""
    set_prices(hass, now, CONTINUOUS_PRICES)
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    yield mock_config_entry
    if mock_config_entry.state is ConfigEntryState.LOADED:
        await hass.config_entries.async_unload(mock_config_entry.entry_id)
        await hass.async_block_till_done()
