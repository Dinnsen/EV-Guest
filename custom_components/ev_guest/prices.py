"""Read electricity prices from a price sensor."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timedelta
from itertools import pairwise
from typing import Any

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import State
from homeassistant.util import dt as dt_util

from .planner import PriceSlot

HOUR = timedelta(hours=1)


def extract_price_slots(state: State | None, now: datetime) -> list[PriceSlot]:
    """Return sorted price slots from a supported price sensor.

    Supported layouts, with hourly, 30 or 15 minute prices:
    - ``raw_today`` / ``raw_tomorrow`` / ``forecast`` lists with ``hour`` and
      ``price`` (Energi Data Service)
    - ``raw_today`` / ``raw_tomorrow`` lists with ``start``, ``end`` and
      ``value`` (Nord Pool from HACS)
    - ``today`` / ``tomorrow`` lists of prices starting at midnight
    """
    if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
        return []

    attrs = state.attributes
    starts: list[tuple[datetime, datetime | None, float]] = []
    for key in ("raw_today", "raw_tomorrow", "forecast"):
        starts.extend(_rows(attrs.get(key)))

    if not starts and isinstance(attrs.get("today"), list):
        base = dt_util.as_local(now).replace(hour=0, minute=0, second=0, microsecond=0)
        for day_offset, key in enumerate(("today", "tomorrow")):
            values = attrs.get(key)
            if not isinstance(values, list) or not values:
                continue
            step = _step_for_day(len(values))
            # Count from midnight in UTC, so days with a DST change line up.
            day = dt_util.as_utc(base + timedelta(days=day_offset))
            for idx, value in enumerate(values):
                price = _to_float(value)
                if price is not None:
                    start = dt_util.as_local(day + step * idx)
                    starts.append((start, start + step, price))

    by_start: dict[datetime, tuple[datetime | None, float]] = {}
    for start, end, price in starts:
        by_start[start] = (end, price)
    ordered = sorted(by_start)
    step = _common_step(ordered)

    slots: list[PriceSlot] = []
    for index, start in enumerate(ordered):
        end, price = by_start[start]
        if end is None or end <= start:
            following = ordered[index + 1] if index + 1 < len(ordered) else None
            end = following if following and following - start <= step else start + step
        slots.append(PriceSlot(start, end, price))
    return slots


def _rows(rows: Any) -> Iterable[tuple[datetime, datetime | None, float]]:
    if not isinstance(rows, list):
        return
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        start = _to_datetime(row.get("hour", row.get("start")))
        price = _to_float(row.get("price", row.get("value")))
        if start is not None and price is not None:
            yield start, _to_datetime(row.get("end")), price


def _common_step(starts: list[datetime]) -> timedelta:
    """The shortest distance between prices, at most one hour."""
    gaps = [later - earlier for earlier, later in pairwise(starts) if later > earlier]
    return min([*gaps, HOUR]) if gaps else HOUR


def _step_for_day(count: int) -> timedelta:
    """Slot length from the number of prices in a day (23-25 hours for DST)."""
    if count >= 88:
        return timedelta(minutes=15)
    if count >= 44:
        return timedelta(minutes=30)
    return HOUR


def _to_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if value in (None, ""):
        return None
    return dt_util.parse_datetime(str(value))


def _to_float(value: object) -> float | None:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
