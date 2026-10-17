"""Tests for the estimated charge level (pure, without Home Assistant)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from custom_components.ev_guest.planner import Segment
from custom_components.ev_guest.progress import SOURCE_METER, SOURCE_PLAN, charged_time, plan_progress

START = datetime(2026, 4, 9, 20, tzinfo=UTC)
# 20 % → 80 % of 77 kWh at 11 kW and 90 %: 51.33 kWh from the grid in 280 minutes.
INPUTS: dict[str, Any] = {
    "soc": 20.0,
    "charge_limit": 80.0,
    "battery_capacity": 77.0,
    "charger_power": 11.0,
    "charging_efficiency": 90.0,
}
PLAN: list[Segment] = [{"start": START, "end": START + timedelta(minutes=280)}]


def test_charged_time_counts_only_the_past() -> None:
    split: list[Segment] = [
        {"start": START, "end": START + timedelta(hours=1)},
        {"start": START + timedelta(hours=3), "end": START + timedelta(hours=4)},
    ]
    assert charged_time(split, START - timedelta(hours=1)) == timedelta()
    assert charged_time(split, START + timedelta(minutes=30)) == timedelta(minutes=30)
    # Paused between the two periods.
    assert charged_time(split, START + timedelta(hours=2)) == timedelta(hours=1)
    assert charged_time(split, START + timedelta(hours=3, minutes=30)) == timedelta(hours=1, minutes=30)
    assert charged_time(split, START + timedelta(hours=9)) == timedelta(hours=2)


def test_without_meter_the_estimate_follows_the_plan() -> None:
    before = plan_progress(PLAN, INPUTS, START - timedelta(hours=1))
    assert before is not None
    assert before.soc == 20
    assert before.source == SOURCE_PLAN
    assert before.behind_plan is None

    one_hour = plan_progress(PLAN, INPUTS, START + timedelta(hours=1))
    assert one_hour is not None
    assert one_hour.planned_energy == pytest.approx(11)
    assert one_hour.soc == pytest.approx(20 + 11 * 0.9 / 77 * 100)
    assert one_hour.start_soc == 20
    assert one_hour.target_soc == 80

    # Never past the target, also after the plan.
    after = plan_progress(PLAN, INPUTS, START + timedelta(hours=8))
    assert after is not None
    assert after.soc == pytest.approx(80)


def test_with_meter_the_estimate_follows_the_energy() -> None:
    on_track = plan_progress(PLAN, INPUTS, START + timedelta(hours=1), measured_energy=10.5)
    assert on_track is not None
    assert on_track.source == SOURCE_METER
    assert on_track.soc == pytest.approx(20 + 10.5 * 0.9 / 77 * 100)
    assert on_track.planned_soc == pytest.approx(20 + 11 * 0.9 / 77 * 100)
    assert on_track.behind_plan is False

    slow = plan_progress(PLAN, INPUTS, START + timedelta(hours=1), measured_energy=5)
    assert slow is not None
    assert slow.behind_plan is True

    # A car that stopped by itself still counts as behind after the plan.
    stopped = plan_progress(PLAN, INPUTS, START + timedelta(hours=6), measured_energy=30)
    assert stopped is not None
    assert stopped.behind_plan is True
    assert stopped.soc == pytest.approx(20 + 30 * 0.9 / 77 * 100)


def test_behind_plan_needs_time_and_a_real_gap() -> None:
    # Too early: a car takes a moment to start, meters report in steps.
    early = plan_progress(PLAN, INPUTS, START + timedelta(minutes=15), measured_energy=0)
    assert early is not None
    assert early.behind_plan is False

    # Less than 1 kWh missing is not a problem, even below 80 %.
    small = {**INPUTS, "charger_power": 1.0}
    gap = plan_progress(PLAN, small, START + timedelta(minutes=30), measured_energy=0)
    assert gap is not None
    assert gap.behind_plan is False


def test_measured_estimate_is_capped() -> None:
    full = plan_progress(PLAN, INPUTS, START + timedelta(hours=1), measured_energy=500)
    assert full is not None
    assert full.soc == 100
    negative = plan_progress(PLAN, INPUTS, START + timedelta(hours=1), measured_energy=-3)
    assert negative is not None
    assert negative.soc == 20


@pytest.mark.parametrize(
    "inputs",
    [
        None,
        {},
        {**INPUTS, "soc": None},
        {**INPUTS, "battery_capacity": "x"},
        {**INPUTS, "battery_capacity": 0},
        {**INPUTS, "charger_power": 0},
    ],
)
def test_no_estimate_without_usable_inputs(inputs: dict[str, Any] | None) -> None:
    assert plan_progress(PLAN, inputs, START) is None


def test_no_estimate_without_plan() -> None:
    assert plan_progress([], INPUTS, START) is None


def test_missing_efficiency_means_no_losses() -> None:
    inputs = {key: value for key, value in INPUTS.items() if key != "charging_efficiency"}
    progress = plan_progress(PLAN, inputs, START + timedelta(hours=1))
    assert progress is not None
    assert progress.soc == pytest.approx(20 + 11 / 77 * 100)
