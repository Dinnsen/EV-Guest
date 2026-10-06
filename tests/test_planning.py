"""Tests for the pure planning helpers."""

from __future__ import annotations

from datetime import datetime, time, timedelta

from homeassistant.core import State
from homeassistant.util import dt as dt_util
import pytest

from custom_components.ev_guest.coordinator import (
    format_time,
    merge_segments,
    next_completion_datetime,
    parse_segments,
    parse_time,
    segments_to_schedule,
    select_continuous_segments,
    select_split_segments,
    serialize_segments,
)
from custom_components.ev_guest.prices import extract_price_slots

START = datetime.fromisoformat("2026-04-09T20:00:00+02:00")


def _slots(prices: list[float]) -> list[tuple[datetime, float]]:
    return [(START + timedelta(hours=i), price) for i, price in enumerate(prices)]


def _hhmm(segments) -> list[tuple[str, str]]:
    return [(seg["start"].strftime("%H:%M"), seg["end"].strftime("%H:%M")) for seg in segments]


def test_continuous_picks_cheapest_block() -> None:
    slots = _slots([1.80, 1.50, 0.40, 0.30, 0.20, 0.25, 0.90, 1.10, 1.30, 1.40, 1.60])
    completion = START.replace(hour=7) + timedelta(days=1)

    segments, cost = select_continuous_segments(slots, 46.2, 4.2, 252, completion)

    assert _hhmm(segments) == [("22:00", "02:12")]
    assert cost == pytest.approx(14.63, rel=1e-3)


def test_continuous_respects_completion_time() -> None:
    slots = _slots([5.0, 5.0, 0.2, 0.1, 0.1])

    # 23:00 is cheaper but would end after the 23:00 completion time.
    segments, _cost = select_continuous_segments(slots, 11, 1.0, 60, START + timedelta(hours=3))

    assert _hhmm(segments) == [("22:00", "23:00")]


def test_continuous_without_room_returns_nothing() -> None:
    assert select_continuous_segments(_slots([1.0]), 22, 2.0, 120, None) == ([], 0.0)


def test_split_puts_part_hour_on_next_cheapest_hour_and_joins_it() -> None:
    slots = _slots([1.80, 0.10, 1.50, 0.20, 1.40, 0.30, 1.30])
    completion = START.replace(hour=7) + timedelta(days=1)

    segments, cost = select_split_segments(slots, 46.2, 4.2, completion)

    # Full hours at 0.10, 0.20, 0.30 and 1.30; 0.2 h at 1.40 joined to 01:00.
    assert cost == pytest.approx(23.98, rel=1e-3)
    assert _hhmm(segments) == [("21:00", "22:00"), ("23:00", "00:00"), ("00:48", "03:00")]


def test_split_part_hour_starts_its_slot_when_next_hour_is_not_charging() -> None:
    slots = _slots([0.1, 9.0, 0.2])

    segments, _cost = select_split_segments(slots, 15, 1.5, None)

    assert _hhmm(segments) == [("20:00", "21:00"), ("22:00", "22:30")]


def test_split_skips_hours_ending_after_completion() -> None:
    slots = _slots([5.0, 5.0, 0.1])

    segments, _cost = select_split_segments(slots, 10, 1.0, START + timedelta(hours=2, minutes=30))

    assert _hhmm(segments) == [("20:00", "21:00")]


def test_split_without_enough_hours_returns_nothing() -> None:
    assert select_split_segments(_slots([1.0]), 20, 2.0, None) == ([], 0.0)


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


def test_schedule_marks_hours_with_charging() -> None:
    segments = [{"start": START + timedelta(minutes=30), "end": START + timedelta(minutes=90)}]

    schedule = segments_to_schedule(segments, _slots([1, 1, 1]))

    assert [row["value"] for row in schedule] == [1.0, 1.0, 0.0]


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


def test_extract_price_slots_raw_lists_with_strings_and_datetimes() -> None:
    state = State(
        "sensor.prices",
        "1.0",
        {
            "raw_today": [{"hour": START, "price": 1.0}, {"hour": "bad", "price": 1}, {"price": 2}],
            "raw_tomorrow": None,
            "forecast": [{"hour": (START + timedelta(hours=1)).isoformat(), "price": "2.5"}],
        },
    )

    assert extract_price_slots(state, START) == [(START, 1.0), (START + timedelta(hours=1), 2.5)]


def test_extract_price_slots_today_tomorrow_arrays() -> None:
    now = dt_util.as_local(START)
    state = State("sensor.prices", "1.0", {"today": [1.0, 2.0], "tomorrow": [3.0, "x"]})

    slots = extract_price_slots(state, now)

    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    assert slots == [(midnight, 1.0), (midnight + timedelta(hours=1), 2.0), (midnight + timedelta(days=1), 3.0)]


@pytest.mark.parametrize("state", [None, State("sensor.prices", "unavailable"), State("sensor.prices", "1", {})])
def test_extract_price_slots_without_prices(state) -> None:
    assert extract_price_slots(state, START) == []


def test_extract_price_slots_today_without_tomorrow() -> None:
    now = dt_util.as_local(START)
    state = State("sensor.prices", "1.0", {"today": [1.0], "tomorrow": None})

    assert len(extract_price_slots(state, now)) == 1
