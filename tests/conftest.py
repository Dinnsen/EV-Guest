"""Shared pytest helpers for EV Guest."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def patch_data_update_coordinator_init(monkeypatch):
    """Patch Home Assistant's DataUpdateCoordinator init for lightweight unit tests.

    Newer Home Assistant versions perform frame-helper checks inside
    DataUpdateCoordinator.__init__, which fail in this stripped-down pytest setup.
    The integration runtime code is not touched; this only affects tests.
    """

    def _fake_init(self, hass, logger, *, name=None, update_interval=None, always_update=True, config_entry=None):
        self.hass = hass
        self.logger = logger
        self.name = name
        self.update_interval = update_interval
        self.always_update = always_update
        self.config_entry = config_entry
        self.data = None
        self.last_update_success = True
        self._listeners = {}

    monkeypatch.setattr(DataUpdateCoordinator, "__init__", _fake_init)


@pytest.fixture(autouse=True)
def patch_storage_and_timers(monkeypatch):
    """Keep coordinator tests free of disk storage and real HA timers."""
    import custom_components.ev_guest.coordinator as coordinator_module

    store = MagicMock()
    store.async_load = AsyncMock(return_value=None)
    store.async_remove = AsyncMock()
    monkeypatch.setattr(coordinator_module, "Store", MagicMock(return_value=store))
    monkeypatch.setattr(
        coordinator_module, "async_track_point_in_time", MagicMock(return_value=MagicMock())
    )
    return store


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
            "country": "Denmark",
            "plate_provider": "motorapi_dk",
        },
        options={},
        runtime_data=None,
        version=7,
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
def hass(mock_hass: MagicMock) -> MagicMock:
    """Alias mock_hass for tests that expect a hass fixture."""
    return mock_hass


@pytest.fixture
def fixed_now(monkeypatch):
    """Freeze dt_util.now() to a fixed Copenhagen-aware datetime."""
    now = dt_util.parse_datetime("2026-04-09T20:00:00+02:00")
    monkeypatch.setattr(dt_util, "now", lambda: now)
    return now
