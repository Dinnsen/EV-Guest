"""Unit tests for EV Guest coordinator logic."""

from __future__ import annotations

from datetime import timedelta, time
from unittest.mock import MagicMock

import pytest

from custom_components.ev_guest.api import VehicleLookupResult
from custom_components.ev_guest.const import (
    INPUT_BATTERY_CAPACITY,
    INPUT_CHARGE_COMPLETION_TIME,
    INPUT_CHARGE_LIMIT,
    INPUT_CHARGER_POWER,
    INPUT_CONTINUOUS_CHARGING_PREFERRED,
    INPUT_ENABLE_CHARGER_CONTROL,
    INPUT_SOC,
    INPUT_USE_COMPLETION_TIME,
    RESULT_CHARGE_COSTS,
    RESULT_CHARGE_END_TIME,
    RESULT_CHARGE_START_TIME,
    RESULT_CHARGE_TIME,
    RESULT_CHARGING_SPEED,
)
from custom_components.ev_guest.coordinator import EVGuestCoordinator


@pytest.fixture
def coordinator(mock_hass, mock_config_entry, fixed_now, monkeypatch) -> EVGuestCoordinator:
    monkeypatch.setattr(
        "custom_components.ev_guest.coordinator.async_get_clientsession",
        lambda hass: MagicMock(),
    )
    return EVGuestCoordinator(mock_hass, mock_config_entry)


def test_merge_vehicle_results_prefers_primary_but_falls_back_missing_fields(
    coordinator: EVGuestCoordinator,
) -> None:
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


def test_format_duration_returns_hours_and_minutes_when_configured(
    coordinator: EVGuestCoordinator,
) -> None:
    coordinator.config_entry.options = {"duration_format": "hours_minutes"}
    assert coordinator._format_duration(131) == "2h 11m"


def test_completion_time_parsing_and_formatting(coordinator: EVGuestCoordinator) -> None:
    coordinator.config_entry.options = {"time_format": "24h"}
    assert coordinator.get_completion_time_text() == "07:00"
    assert coordinator._parse_completion_time("10:15 PM") == time(hour=22, minute=15)

    coordinator.config_entry.options = {"time_format": "12h"}
    coordinator.data.inputs[INPUT_CHARGE_COMPLETION_TIME] = "22:15"
    assert coordinator.get_completion_time_text() == "10:15 PM"


def test_calculate_schedule_finds_cheapest_window_from_price_slots(
    coordinator: EVGuestCoordinator,
) -> None:
    coordinator.data.inputs.update(
        {
            INPUT_SOC: 20,
            INPUT_BATTERY_CAPACITY: 77,
            INPUT_CHARGER_POWER: 11,
            INPUT_CHARGE_LIMIT: 80,
            INPUT_CHARGE_COMPLETION_TIME: "07:00",
            INPUT_USE_COMPLETION_TIME: True,
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
    assert result[RESULT_CHARGE_END_TIME] == "02:12"
    assert result[RESULT_CHARGE_COSTS] == pytest.approx(14.63, rel=1e-2)


def test_calculate_schedule_raises_when_charge_limit_is_not_above_soc(
    coordinator: EVGuestCoordinator,
) -> None:
    coordinator.data.inputs.update(
        {
            INPUT_SOC: 80,
            INPUT_BATTERY_CAPACITY: 77,
            INPUT_CHARGER_POWER: 11,
            INPUT_CHARGE_LIMIT: 80,
            INPUT_CHARGE_COMPLETION_TIME: "07:00",
        }
    )

    with pytest.raises(ValueError, match="Charge limit must be above current SoC"):
        coordinator._calculate_schedule()


def test_calculate_schedule_can_split_when_continuous_is_off(
    coordinator: EVGuestCoordinator,
) -> None:
    coordinator.data.inputs.update(
        {
            INPUT_SOC: 20,
            INPUT_BATTERY_CAPACITY: 77,
            INPUT_CHARGER_POWER: 11,
            INPUT_CHARGE_LIMIT: 80,
            INPUT_CHARGE_COMPLETION_TIME: "07:00",
            INPUT_USE_COMPLETION_TIME: True,
            INPUT_CONTINUOUS_CHARGING_PREFERRED: False,
            INPUT_ENABLE_CHARGER_CONTROL: False,
        }
    )
    coordinator.hass.states.get.return_value = MagicMock(
        state="1.21",
        attributes={
            "forecast": [
                {"hour": "2026-04-09T20:00:00+02:00", "price": 1.80},
                {"hour": "2026-04-09T21:00:00+02:00", "price": 0.10},
                {"hour": "2026-04-09T22:00:00+02:00", "price": 1.50},
                {"hour": "2026-04-09T23:00:00+02:00", "price": 0.20},
                {"hour": "2026-04-10T00:00:00+02:00", "price": 1.40},
                {"hour": "2026-04-10T01:00:00+02:00", "price": 0.30},
                {"hour": "2026-04-10T02:00:00+02:00", "price": 1.30},
            ],
        },
    )

    result = coordinator._calculate_schedule()

    assert result[RESULT_CHARGE_COSTS] == pytest.approx(24.86, rel=1e-2)
    assert coordinator.data.results["plan_mode"] == "split"


def test_charge_now_is_true_inside_active_schedule(
    coordinator: EVGuestCoordinator, fixed_now
) -> None:
    coordinator.data.results["charging_schedule"] = [
        {"start": "2026-04-09T19:00:00+02:00", "value": 0},
        {"start": "2026-04-09T20:00:00+02:00", "value": 1},
        {"start": "2026-04-09T21:00:00+02:00", "value": 0},
    ]

    assert coordinator.is_charge_now() is True


def test_read_charger_status_prefers_configured_status_entity(
    coordinator: EVGuestCoordinator,
) -> None:
    coordinator.hass.states.get.return_value = MagicMock(state="on")
    assert coordinator._read_charger_status() is True


def test_calculate_schedule_without_completion_time_uses_visible_two_day_horizon(
    coordinator: EVGuestCoordinator, fixed_now
) -> None:
    coordinator.data.inputs.update(
        {
            INPUT_SOC: 0,
            INPUT_BATTERY_CAPACITY: 10,
            INPUT_CHARGER_POWER: 10,
            INPUT_CHARGE_LIMIT: 10,
            INPUT_USE_COMPLETION_TIME: False,
            INPUT_CONTINUOUS_CHARGING_PREFERRED: False,
            INPUT_ENABLE_CHARGER_CONTROL: False,
        }
    )

    forecast = []
    for offset in range(48):
        forecast.append(
            {
                "hour": (fixed_now + timedelta(hours=offset)).isoformat(),
                "price": 1.0,
            }
        )
    forecast.append(
        {
            "hour": (fixed_now + timedelta(hours=48)).isoformat(),
            "price": 0.01,
        }
    )

    coordinator.hass.states.get.return_value = MagicMock(
        state="1.00",
        attributes={"forecast": forecast},
    )

    result = coordinator._calculate_schedule()

    assert result[RESULT_CHARGE_START_TIME] == "20:00"
    assert len(coordinator.data.results["raw_two_days"]) == 48
    assert any(
        entry["value"] == 1.0
        for entry in coordinator.data.results["charging_schedule"]
    )
