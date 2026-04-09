"""Unit tests for EV Guest coordinator logic."""

from __future__ import annotations

from datetime import time
from unittest.mock import MagicMock

import pytest
from homeassistant.util import dt as dt_util

from custom_components.ev_guest.api import VehicleLookupResult
from custom_components.ev_guest.const import (
    ATTR_FUEL_TYPE,
    ATTR_MODEL_YEAR,
    ATTR_VIN,
    INPUT_BATTERY_CAPACITY,
    INPUT_CHARGE_COMPLETION_TIME,
    INPUT_CHARGE_LIMIT,
    INPUT_CHARGER_POWER,
    INPUT_SOC,
    RESULT_CHARGE_COSTS,
    RESULT_CHARGE_END_TIME,
    RESULT_CHARGE_START_TIME,
    RESULT_CHARGE_TIME,
    RESULT_CHARGING_SPEED,
)
from custom_components.ev_guest.coordinator import EVGuestCoordinator


@pytest.fixture
def coordinator(mock_hass, mock_config_entry, fixed_now, monkeypatch) -> EVGuestCoordinator:
    """Create a coordinator with a mocked HTTP session."""
    monkeypatch.setattr(
        "custom_components.ev_guest.coordinator.async_get_clientsession",
        lambda hass: MagicMock(),
    )
    return EVGuestCoordinator(mock_hass, mock_config_entry)


def test_merge_vehicle_results_prefers_primary_but_falls_back_missing_fields(coordinator: EVGuestCoordinator) -> None:
    primary = VehicleLookupResult(
        plate="EN17765",
        vin="",
        brand="Mercedes",
        model="EQB",
        variant=None,
        model_year=None,
        fuel_type=None,
        source="MotorAPI",
        raw={},
    )
    fallback = VehicleLookupResult(
        plate="",
        vin="W1N1234567890",
        brand="Mercedes-Benz",
        model="EQB",
        variant="250+",
        model_year=2024,
        fuel_type="Electric",
        source="NHTSA vPIC",
        raw={},
    )

    merged = coordinator._merge_vehicle_results(primary, fallback)

    assert merged.brand == "Mercedes"
    assert merged.model == "EQB"
    assert merged.variant == "250+"
    assert merged.model_year == 2024
    assert merged.fuel_type == "Electric"
    assert merged.vin == "W1N1234567890"


def test_format_duration_returns_minutes_by_default(coordinator: EVGuestCoordinator) -> None:
    assert coordinator._format_duration(131) == 131


def test_format_duration_returns_hours_and_minutes_when_configured(coordinator: EVGuestCoordinator) -> None:
    coordinator.config_entry.options = {"duration_format": "hours_minutes"}
    assert coordinator._format_duration(131) == "2h 11m"


def test_next_completion_datetime_moves_to_next_day_when_time_has_passed(coordinator: EVGuestCoordinator, fixed_now) -> None:
    result = coordinator._next_completion_datetime(fixed_now, time(hour=7, minute=0))
    assert result.isoformat() == "2026-04-10T07:00:00+02:00"


def test_calculate_schedule_finds_cheapest_window_from_price_slots(coordinator: EVGuestCoordinator) -> None:
    coordinator.data.inputs.update(
        {
            INPUT_SOC: 20,
            INPUT_BATTERY_CAPACITY: 77,
            INPUT_CHARGER_POWER: 11,
            INPUT_CHARGE_LIMIT: 80,
            INPUT_CHARGE_COMPLETION_TIME: time(hour=7, minute=0),
        }
    )
    coordinator.hass.states.get.return_value = MagicMock(
        state="1.21",
        attributes={
            "raw_today": [
                {"hour": "2026-04-09T20:00:00+02:00", "price": 1.80},
                {"hour": "2026-04-09T21:00:00+02:00", "price": 1.50},
                {"hour": "2026-04-09T22:00:00+02:00", "price": 0.40},
                {"hour": "2026-04-09T23:00:00+02:00", "price": 0.30},
            ],
            "forecast": [
                {"hour": "2026-04-10T00:00:00+02:00", "price": 0.20},
                {"hour": "2026-04-10T01:00:00+02:00", "price": 0.25},
                {"hour": "2026-04-10T02:00:00+02:00", "price": 0.90},
                {"hour": "2026-04-10T03:00:00+02:00", "price": 1.10},
                {"hour": "2026-04-10T04:00:00+02:00", "price": 1.30},
                {"hour": "2026-04-10T05:00:00+02:00", "price": 1.40},
                {"hour": "2026-04-10T06:00:00+02:00", "price": 1.60},
            ],
        },
    )

    result = coordinator._calculate_schedule()

    assert result[RESULT_CHARGING_SPEED] == pytest.approx(14.3, rel=1e-2)
    assert result[RESULT_CHARGE_TIME] == 252
    assert result[RESULT_CHARGE_START_TIME] == "22:00"
    assert result[RESULT_CHARGE_END_TIME] == "02:00"
    assert result[RESULT_CHARGE_COSTS] == pytest.approx(17.09, rel=1e-2)


def test_calculate_schedule_raises_when_charge_limit_is_not_above_soc(coordinator: EVGuestCoordinator) -> None:
    coordinator.data.inputs.update(
        {
            INPUT_SOC: 80,
            INPUT_BATTERY_CAPACITY: 77,
            INPUT_CHARGER_POWER: 11,
            INPUT_CHARGE_LIMIT: 80,
            INPUT_CHARGE_COMPLETION_TIME: time(hour=7, minute=0),
        }
    )

    with pytest.raises(ValueError, match="Charge limit must be above current SoC"):
        coordinator._calculate_schedule()
