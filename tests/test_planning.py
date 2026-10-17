"""Tests for the pure planning helpers and the price sensor reader."""

from __future__ import annotations

from datetime import datetime, time, timedelta

from homeassistant.core import State
from homeassistant.util import dt as dt_util
import pytest

from custom_components.ev_guest.coordinator import (
    format_time,
    meter_kwh,
    next_completion_datetime,
    parse_segments,
    parse_time,
    serialize_segments,
)
from custom_components.ev_guest.planner import (
    ChargeNeed,
    PlanError,
    PriceSlot,
    charge_need,
    energy_cost,
    limit_slots,
    make_plan,
    merge_segments,
    price_at,
    segments_to_schedule,
    select_continuous,
    select_split,
)
from custom_components.ev_guest.prices import extract_price_slots

START = datetime.fromisoformat("2026-04-09T20:00:00+02:00")
TWO_DAYS = timedelta(hours=48)


def _slots(prices: list[float], minutes: int = 60, start: datetime = START) -> list[PriceSlot]:
    step = timedelta(minutes=minutes)
    return [PriceSlot(start + step * i, start + step * (i + 1), price) for i, price in enumerate(prices)]


def _hhmm(segments) -> list[tuple[str, str]]:
    return [(seg["start"].strftime("%H:%M"), seg["end"].strftime("%H:%M")) for seg in segments]


def _need(hours: float, power: float = 11) -> ChargeNeed:
    return ChargeNeed(hours * power, hours * power, hours, round(hours * 60), 10)


CONTINUOUS = [1.80, 1.50, 0.40, 0.30, 0.20, 0.25, 0.90, 1.10, 1.30, 1.40, 1.60]


def test_charge_need_with_and_without_losses() -> None:
    lossless = charge_need(20, 80, 77, 11, 1.0)
    assert lossless.minutes == 252
    assert lossless.speed_pct_per_hour == pytest.approx(14.29, rel=1e-3)

    need = charge_need(20, 80, 77, 11, 0.9)
    assert need.battery_kwh == pytest.approx(46.2)
    assert need.grid_kwh == pytest.approx(51.33, rel=1e-3)
    assert need.minutes == 280
    assert need.speed_pct_per_hour == pytest.approx(12.86, rel=1e-3)


@pytest.mark.parametrize(
    ("args", "key"),
    [
        ((80, 80, 77, 11, 0.9), "limit_not_above_soc"),
        ((20, 80, 0, 11, 0.9), "invalid_input"),
        ((20, 80, 77, 0, 0.9), "invalid_input"),
        ((20, 80, 77, 11, 0), "invalid_input"),
        ((-1, 80, 77, 11, 0.9), "invalid_input"),
    ],
)
def test_charge_need_rejects_bad_input(args, key) -> None:
    with pytest.raises(PlanError) as err:
        charge_need(*args)
    assert err.value.key == key


def test_continuous_picks_cheapest_block() -> None:
    segments, cost = select_continuous(_slots(CONTINUOUS), charge_need(20, 80, 77, 11, 1.0), 11)

    assert _hhmm(segments) == [("22:00", "02:12")]
    assert cost == pytest.approx(14.63, rel=1e-3)


def test_continuous_can_end_with_a_slot() -> None:
    """The partial slot goes first when the block is cheaper that way."""
    segments, cost = select_continuous(_slots([5.0, 0.5, 0.1, 9.0]), _need(1.5), 11)

    assert _hhmm(segments) == [("21:30", "23:00")]
    assert cost == pytest.approx(11 * (0.5 * 0.5 + 0.1))


def test_continuous_respects_completion_time() -> None:
    slots = limit_slots(_slots([5.0, 5.0, 0.2, 0.1, 0.1]), START, START + timedelta(hours=3))

    segments, _cost = select_continuous(slots, _need(1), 11)

    assert _hhmm(segments) == [("22:00", "23:00")]


def test_continuous_without_room_returns_nothing() -> None:
    assert select_continuous(_slots([1.0]), _need(2), 11) == ([], 0.0)


def test_continuous_does_not_cross_a_gap() -> None:
    slots = [*_slots([0.1]), *_slots([0.1], start=START + timedelta(hours=2))]

    assert select_continuous(slots, _need(1.5), 11) == ([], 0.0)


def test_continuous_with_quarter_hour_prices() -> None:
    prices = [1.0] * 8 + [0.2, 0.1, 0.1, 0.2] + [1.0] * 8

    segments, cost = select_continuous(_slots(prices, 15), _need(1), 11)

    assert _hhmm(segments) == [("22:00", "23:00")]
    assert cost == pytest.approx(11 * 0.15)


def test_split_puts_part_slot_on_next_cheapest_and_joins_it() -> None:
    slots = _slots([1.80, 0.10, 1.50, 0.20, 1.40, 0.30, 1.30])

    segments, cost = select_split(slots, charge_need(20, 80, 77, 11, 1.0), 11)

    # Full hours at 0.10, 0.20, 0.30 and 1.30; 0.2 h at 1.40 joined to 01:00.
    assert cost == pytest.approx(23.98, rel=1e-3)
    assert _hhmm(segments) == [("21:00", "22:00"), ("23:00", "00:00"), ("00:48", "03:00")]


def test_split_part_slot_starts_its_slot_when_next_is_not_charging() -> None:
    segments, _cost = select_split(_slots([0.1, 9.0, 0.2]), _need(1.5, 10), 10)

    assert _hhmm(segments) == [("20:00", "21:00"), ("22:00", "22:30")]


def test_split_with_quarter_hour_prices() -> None:
    segments, cost = select_split(_slots([0.3, 0.1, 0.9, 0.1, 0.2], 15), _need(0.6), 11)

    # Two quarters at 0.10, then 6 minutes at 0.20 joined to the second.
    assert _hhmm(segments) == [("20:15", "20:30"), ("20:45", "21:06")]
    assert cost == pytest.approx(11 * (0.25 * 0.1 + 0.25 * 0.1 + 0.1 * 0.2))


def test_split_without_enough_slots_returns_nothing() -> None:
    assert select_split(_slots([1.0]), _need(2), 11) == ([], 0.0)


def test_limit_slots_starts_the_current_slot_now() -> None:
    now = START + timedelta(minutes=10, seconds=5)

    slots = limit_slots(_slots([0.1, 5.0]), now, START + timedelta(hours=1, minutes=30))

    assert [(slot.start.strftime("%H:%M"), slot.end.strftime("%H:%M")) for slot in slots] == [
        ("20:11", "21:00"),
        ("21:00", "21:30"),
    ]


def test_energy_cost_needs_every_price() -> None:
    slots = _slots([1.0, 2.0])
    assert energy_cost(slots, START, START + timedelta(hours=1.5), 10) == pytest.approx(20)
    assert energy_cost(slots, START, START + timedelta(hours=3), 10) is None


def test_make_plan_with_savings() -> None:
    need = charge_need(20, 80, 77, 11, 0.9)

    plan = make_plan(_slots(CONTINUOUS), need, 11, START, START + timedelta(hours=11), TWO_DAYS, True)

    assert plan.mode == "continuous"
    assert plan.cost == pytest.approx(19.25)
    assert plan.charge_now_cost == pytest.approx(11 * (1.8 + 1.5 + 0.4 + 0.3 + 0.2 * 2 / 3))
    assert plan.savings == pytest.approx(plan.charge_now_cost - plan.cost)
    assert plan.average_price == pytest.approx(19.25 / need.grid_kwh)


def test_make_plan_split_mode() -> None:
    plan = make_plan(_slots([0.1, 9.0, 0.2]), _need(1.5, 10), 10, START, None, TWO_DAYS, False)
    assert plan.mode == "split"


def test_make_plan_without_charge_now_price() -> None:
    """Prices that start later give no savings figure."""
    later = _slots([1.0] * 5, start=START + timedelta(hours=1))

    plan = make_plan(later, _need(1), 11, START, None, TWO_DAYS, True)

    assert plan.charge_now_cost is None
    assert plan.savings is None


@pytest.mark.parametrize(
    ("prices", "completion", "key"),
    [
        ([], None, "no_price_data"),
        ([1.0, 1.0], timedelta(hours=11), "not_enough_prices"),
        ([1.0, 1.0, 1.0, 1.0], timedelta(hours=2, minutes=30), "no_window"),
    ],
)
def test_make_plan_errors(prices, completion, key) -> None:
    with pytest.raises(PlanError) as err:
        make_plan(_slots(prices), _need(3), 11, START, START + completion if completion else None, TWO_DAYS, True)
    assert err.value.key == key


def test_make_plan_no_window_when_blocks_are_split_by_gaps() -> None:
    slots = [*_slots([0.1, 0.1]), *_slots([0.1, 0.1], start=START + timedelta(hours=3))]

    with pytest.raises(PlanError) as err:
        make_plan(slots, _need(3), 11, START, None, TWO_DAYS, True)
    assert err.value.key == "no_window"


def test_merge_segments_joins_overlapping_and_adjacent() -> None:
    a = {"start": START, "end": START + timedelta(hours=1)}
    b = {"start": START + timedelta(hours=1), "end": START + timedelta(hours=2)}
    c = {"start": START + timedelta(hours=3), "end": START + timedelta(hours=4)}

    assert merge_segments([c, b, a]) == [
        {"start": START, "end": START + timedelta(hours=2)},
        c,
    ]


def test_segments_round_trip_and_bad_rows_are_dropped() -> None:
    segments = [{"start": START, "end": START + timedelta(minutes=95)}]
    raw = [
        *serialize_segments(segments),
        {"start": "x"},
        "nope",
        {"start": START.isoformat(), "end": START.isoformat()},
    ]

    assert parse_segments(raw) == segments


def test_schedule_marks_slots_with_charging() -> None:
    segments = [{"start": START + timedelta(minutes=30), "end": START + timedelta(minutes=90)}]

    schedule = segments_to_schedule(segments, _slots([1, 1, 1]))

    assert [row["value"] for row in schedule] == [1.0, 1.0, 0.0]


def test_price_at() -> None:
    slots = _slots([1.0, 2.0])
    assert price_at(slots, START + timedelta(minutes=70)) == 2.0
    assert price_at(slots, START + timedelta(hours=3)) is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("07:00", time(7)),
        ("22:15:00", time(22, 15)),
        ("10:15 PM", time(22, 15)),
        (time(6, 30), time(6, 30)),
        ("bad", None),
        (None, None),
    ],
)
def test_parse_time(value, expected) -> None:
    assert parse_time(value) == expected


def test_format_time_defaults_to_seven() -> None:
    assert format_time(time(6, 5)) == "06:05"
    assert format_time(None) == "07:00"


def test_next_completion_is_today_or_tomorrow() -> None:
    assert next_completion_datetime(START, time(23)) == START.replace(hour=23)
    assert next_completion_datetime(START, time(7)) == START.replace(hour=7) + timedelta(days=1)
    assert next_completion_datetime(START, time(20)) == START + timedelta(days=1)


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        (State("sensor.meter", "12.5", {"unit_of_measurement": "kWh"}), 12.5),
        (State("sensor.meter", "12500", {"unit_of_measurement": "Wh"}), 12.5),
        (State("sensor.meter", "0.0125", {"unit_of_measurement": "MWh"}), 12.5),
        (State("sensor.meter", "unavailable"), None),
        (State("sensor.meter", "x"), None),
        (None, None),
    ],
)
def test_meter_kwh(state, expected) -> None:
    assert meter_kwh(state) == (pytest.approx(expected) if expected is not None else None)


# ----------------------------------------------------------------------
# Price sensors


def test_extract_price_slots_energi_data_service() -> None:
    state = State(
        "sensor.prices",
        "1.0",
        {
            "raw_today": [{"hour": START, "price": 1.0}, {"hour": "bad", "price": 1}, {"price": 2}],
            "raw_tomorrow": None,
            "forecast": [{"hour": (START + timedelta(hours=1)).isoformat(), "price": "2.5"}],
        },
    )

    assert extract_price_slots(state, START) == [
        PriceSlot(START, START + timedelta(hours=1), 1.0),
        PriceSlot(START + timedelta(hours=1), START + timedelta(hours=2), 2.5),
    ]


def test_extract_price_slots_quarter_hours() -> None:
    rows = [{"hour": START + timedelta(minutes=15 * i), "price": i} for i in range(4)]

    slots = extract_price_slots(State("sensor.prices", "1", {"raw_today": rows}), START)

    assert [slot.hours for slot in slots] == [0.25] * 4
    assert slots[-1].end == START + timedelta(hours=1)


def test_extract_price_slots_nord_pool() -> None:
    rows = [
        {"start": START.isoformat(), "end": (START + timedelta(minutes=15)).isoformat(), "value": 0.5},
        {"start": START + timedelta(minutes=15), "end": START + timedelta(minutes=30), "value": None},
    ]

    slots = extract_price_slots(State("sensor.nordpool", "1", {"raw_today": rows, "raw_tomorrow": []}), START)

    assert slots == [PriceSlot(START, START + timedelta(minutes=15), 0.5)]


def test_extract_price_slots_today_tomorrow_arrays() -> None:
    now = dt_util.as_local(START)
    state = State("sensor.prices", "1.0", {"today": [1.0, 2.0], "tomorrow": [3.0, "x"]})

    slots = extract_price_slots(state, now)

    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    hour = timedelta(hours=1)
    assert [(slot.start, slot.price) for slot in slots] == [
        (midnight, 1.0),
        (midnight + hour, 2.0),
        (midnight + timedelta(days=1), 3.0),
    ]
    assert all(slot.end - slot.start == hour for slot in slots)


def test_extract_price_slots_today_array_with_quarter_hours() -> None:
    now = dt_util.as_local(START)

    slots = extract_price_slots(State("sensor.prices", "1", {"today": [1.0] * 96}), now)

    assert len(slots) == 96
    assert slots[1].start - slots[0].start == timedelta(minutes=15)


@pytest.mark.parametrize("state", [None, State("sensor.prices", "unavailable"), State("sensor.prices", "1", {})])
def test_extract_price_slots_without_prices(state) -> None:
    assert extract_price_slots(state, START) == []


def test_extract_price_slots_today_without_tomorrow() -> None:
    now = dt_util.as_local(START)
    state = State("sensor.prices", "1.0", {"today": [1.0], "tomorrow": None})

    assert len(extract_price_slots(state, now)) == 1
