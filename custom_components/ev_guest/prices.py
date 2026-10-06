"""Read hourly prices from a price sensor."""

from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import State
from homeassistant.util import dt as dt_util

type PriceSlot = tuple[datetime, float]


def extract_price_slots(state: State | None, now: datetime) -> list[PriceSlot]:
    """Return sorted (start, price) slots from a supported price sensor.

    Supported layouts:
    - ``raw_today`` / ``raw_tomorrow`` / ``forecast`` lists with ``hour`` + ``price``
    - ``today`` / ``tomorrow`` lists of hourly prices starting at midnight
    """
    if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
        return []

    attrs = state.attributes
    slots: list[PriceSlot] = []

    for key in ("raw_today", "raw_tomorrow", "forecast"):
        for row in attrs.get(key) or []:
            if not isinstance(row, dict) or row.get("hour") is None or row.get("price") is None:
                continue
            start = row["hour"] if isinstance(row["hour"], datetime) else dt_util.parse_datetime(str(row["hour"]))
            price = _to_float(row["price"])
            if start is not None and price is not None:
                slots.append((start, price))

    if not slots and isinstance(attrs.get("today"), list):
        base = now.replace(hour=0, minute=0, second=0, microsecond=0)
        for day_offset, key in enumerate(("today", "tomorrow")):
            values = attrs.get(key)
            if not isinstance(values, list):
                continue
            day = base + timedelta(days=day_offset)
            for idx, value in enumerate(values):
                price = _to_float(value)
                if price is not None:
                    slots.append((day + timedelta(hours=idx), price))

    deduped = {start.isoformat(): (start, price) for start, price in slots}
    return sorted(deduped.values(), key=lambda slot: slot[0])


def _to_float(value: object) -> float | None:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
