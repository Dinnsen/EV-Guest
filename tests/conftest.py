"""Shared pytest helpers for EV Guest."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.util import dt as dt_util

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def mock_config_entry() -> SimpleNamespace:
    """Return a lightweight config entry stub for unit-style tests."""
    return SimpleNamespace(
        entry_id="test-entry-id",
        title="EV Guest",
        data={
            "price_entity": "sensor.energi_data_service",
            "currency": "DKK",
            "time_format": "24h",
            "duration_format": "minutes",
            "motorapi_api_key": "test-key",
            "charger_switch_entity": "switch.test_charger",
            "charger_status_entity": "binary_sensor.test_charger_status",
            "language": "English",
            "country": "Denmark",
            "plate_provider": "motorapi_dk",
        },
        options={},
        runtime_data=None,
        version=5,
        minor_version=0,
    )


@pytest.fixture
def mock_hass() -> MagicMock:
    """Return a lightweight Home Assistant stub for unit-style tests."""
    hass = MagicMock()
    hass.states = MagicMock()
    hass.async_create_task = MagicMock()
    hass.services = MagicMock()
    hass.services.async_call = AsyncMock()
    hass.config_entries = MagicMock()
    hass.config_entries.async_update_entry = MagicMock()
    return hass


@pytest.fixture
def fixed_now(monkeypatch):
    """Freeze dt_util.now() to a fixed Copenhagen-aware datetime."""
    now = dt_util.parse_datetime("2026-04-09T20:00:00+02:00")
    monkeypatch.setattr(dt_util, "now", lambda: now)
    return now
