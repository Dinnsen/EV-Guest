"""Charging plans from electricity prices.

Pure Python without Home Assistant imports, so the planning rules can be
tested and reasoned about on their own. Prices come as slots of any length
(hourly, 30 or 15 minutes); a plan is a list of charging segments.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from math import ceil

# Costs closer than this are treated as equal, so a later window never
# replaces an earlier one only because of floating point noise.
EPSILON = 1e-9

MODE_CONTINUOUS = "continuous"
MODE_SPLIT = "split"


@dataclass(frozen=True, slots=True)
class PriceSlot:
    """A price valid from ``start`` until ``end``."""

    start: datetime
    end: datetime
    price: float

    @property
    def hours(self) -> float:
        return (self.end - self.start).total_seconds() / 3600


type Segment = dict[str, datetime]


class PlanError(Exception):
    """A charging plan could not be made; ``key`` is a status/translation key."""

    def __init__(self, key: str) -> None:
        super().__init__(key)
        self.key = key


@dataclass(frozen=True, slots=True)
class ChargeNeed:
    """What the car needs, independent of prices."""

    battery_kwh: float
    """Energy that ends up in the battery."""
    grid_kwh: float
    """Energy taken from the grid, including charging losses."""
    hours: float
    """Exact charging time at the charger power."""
    minutes: int
    """Charging time rounded up to whole minutes."""
    speed_pct_per_hour: float
    """Charge level gained per hour."""


@dataclass(slots=True)
class Plan:
    """A charging plan and what it costs."""

    segments: list[Segment]
    cost: float
    mode: str
    need: ChargeNeed
    charge_now_cost: float | None = None
    """Cost when charging starts right away, for the savings figure."""
    average_price: float | None = field(default=None)

    @property
    def savings(self) -> float | None:
        if self.charge_now_cost is None:
            return None
        return max(0.0, self.charge_now_cost - self.cost)


def charge_need(soc: float, limit: float, battery_kwh: float, charger_kw: float, efficiency: float) -> ChargeNeed:
    """Energy and time needed to charge from ``soc`` to ``limit`` (both in %).

    ``efficiency`` is the share (0-1] of the grid energy that reaches the
    battery. The charger power is what the charger draws from the grid.
    """
    if battery_kwh <= 0 or charger_kw <= 0 or not 0 < efficiency <= 1 or not 0 <= soc <= 100 or not 0 <= limit <= 100:
        raise PlanError("invalid_input")
    if limit <= soc:
        raise PlanError("limit_not_above_soc")

    battery = battery_kwh * (limit - soc) / 100
    grid = battery / efficiency
    hours = grid / charger_kw
    return ChargeNeed(
        battery_kwh=battery,
        grid_kwh=grid,
        hours=hours,
        minutes=ceil(hours * 60 - EPSILON),
        speed_pct_per_hour=charger_kw * efficiency / battery_kwh * 100,
    )


def ceil_minute(moment: datetime) -> datetime:
    """``moment`` rounded up to a whole minute."""
    whole = moment.replace(second=0, microsecond=0)
    return whole if whole == moment else whole + timedelta(minutes=1)


def limit_slots(slots: list[PriceSlot], start: datetime, end: datetime | None) -> list[PriceSlot]:
    """Cut slots to the period from ``start`` (rounded up to a minute) to ``end``.

    The slot that is running now is kept from ``start``, so a plan can begin
    right away instead of at the next whole slot.
    """
    start = ceil_minute(start)
    result: list[PriceSlot] = []
    for slot in slots:
        begin = max(slot.start, start)
        stop = min(slot.end, end) if end else slot.end
        if stop > begin:
            result.append(PriceSlot(begin, stop, slot.price))
    return result


def contiguous_runs(slots: list[PriceSlot]) -> list[list[PriceSlot]]:
    """Group sorted slots into runs without gaps."""
    runs: list[list[PriceSlot]] = []
    for slot in slots:
        if runs and runs[-1][-1].end == slot.start:
            runs[-1].append(slot)
        else:
            runs.append([slot])
    return runs


def energy_cost(slots: list[PriceSlot], start: datetime, end: datetime, power_kw: float) -> float | None:
    """Cost of drawing ``power_kw`` from ``start`` to ``end``; None if a price is missing."""
    covered = 0.0
    price_hours = 0.0
    for slot in slots:
        begin = max(slot.start, start)
        stop = min(slot.end, end)
        if stop > begin:
            hours = (stop - begin).total_seconds() / 3600
            covered += hours
            price_hours += slot.price * hours
    wanted = (end - start).total_seconds() / 3600
    if covered + EPSILON < wanted:
        return None
    return price_hours * power_kw


def select_continuous(slots: list[PriceSlot], need: ChargeNeed, power_kw: float) -> tuple[list[Segment], float]:
    """Cheapest single block. Tries blocks that start or end at a slot boundary."""
    exact = timedelta(hours=need.hours)
    rounded = timedelta(minutes=need.minutes)
    best: tuple[datetime, datetime, float] | None = None
    for run in contiguous_runs(slots):
        run_start, run_end = run[0].start, run[-1].end
        candidates: list[tuple[datetime, datetime, datetime]] = []
        for slot in run:
            # Starting with a slot: the last slot may be used in part.
            if slot.start + rounded <= run_end:
                candidates.append((slot.start, slot.start + rounded, slot.start + exact))
            # Ending with a slot: the first slot may be used in part.
            if slot.end - rounded >= run_start:
                candidates.append((slot.end - rounded, slot.end, slot.end))
        for begin, finish, energy_end in sorted(candidates):
            energy_start = energy_end - exact
            cost = energy_cost(run, energy_start, energy_end, power_kw)
            if cost is not None and (best is None or cost < best[2] - EPSILON):
                best = (begin, finish, cost)
    if best is None:
        return [], 0.0
    return [{"start": best[0], "end": best[1]}], best[2]


def select_split(slots: list[PriceSlot], need: ChargeNeed, power_kw: float) -> tuple[list[Segment], float]:
    """Cheapest slots, not necessarily adjacent.

    Whole slots go to the cheapest prices. What is left goes to the next
    cheapest slot, placed against a chosen neighbour so it does not leave a
    gap.
    """
    remaining = need.hours
    chosen_starts: set[datetime] = set()
    segments: list[Segment] = []
    cost = 0.0
    for slot in sorted(slots, key=lambda item: (item.price, item.start)):
        if remaining <= EPSILON:
            break
        if slot.hours <= remaining + EPSILON:
            segments.append({"start": slot.start, "end": slot.end})
            chosen_starts.add(slot.start)
            cost += slot.price * slot.hours * power_kw
            remaining -= slot.hours
            continue
        # Slot boundaries are whole minutes, so the rounded part still fits.
        length = timedelta(minutes=ceil(remaining * 60 - EPSILON))
        if slot.end in chosen_starts:
            # Join the following charging slot.
            segments.append({"start": slot.end - length, "end": slot.end})
        else:
            # Start of the slot: joins a preceding charging slot, if any.
            segments.append({"start": slot.start, "end": slot.start + length})
        cost += slot.price * remaining * power_kw
        remaining = 0.0
    if remaining > EPSILON:
        return [], 0.0
    return merge_segments(segments), cost


def make_plan(
    prices: list[PriceSlot],
    need: ChargeNeed,
    power_kw: float,
    now: datetime,
    completion: datetime | None,
    horizon: timedelta,
    continuous: bool,
) -> Plan:
    """The cheapest plan before ``completion`` (or within ``horizon`` from now)."""
    if not prices:
        raise PlanError("no_price_data")
    deadline = completion or now + horizon
    slots = limit_slots(prices, now, deadline)
    available = sum(slot.hours for slot in slots)
    if available + EPSILON < need.hours:
        # Prices that reach the deadline mean the deadline is the problem,
        # otherwise more prices may still arrive.
        if completion and prices[-1].end >= completion:
            raise PlanError("no_window")
        raise PlanError("not_enough_prices")

    if continuous:
        segments, cost = select_continuous(slots, need, power_kw)
        mode = MODE_CONTINUOUS
    else:
        segments, cost = select_split(slots, need, power_kw)
        mode = MODE_SPLIT
    if not segments:
        raise PlanError("no_window")

    # Charging straight away, with every price known (deadline ignored).
    upcoming = limit_slots(prices, now, None)
    charge_now_cost = None
    if upcoming and upcoming[0].start == ceil_minute(now):
        begin = upcoming[0].start
        charge_now_cost = energy_cost(upcoming, begin, begin + timedelta(hours=need.hours), power_kw)

    return Plan(
        segments=segments,
        cost=cost,
        mode=mode,
        need=need,
        charge_now_cost=charge_now_cost,
        average_price=cost / need.grid_kwh if need.grid_kwh else None,
    )


def merge_segments(segments: list[Segment]) -> list[Segment]:
    """Join overlapping and adjacent segments."""
    merged: list[Segment] = []
    for segment in sorted(segments, key=lambda seg: seg["start"]):
        if merged and segment["start"] <= merged[-1]["end"]:
            merged[-1]["end"] = max(merged[-1]["end"], segment["end"])
        else:
            merged.append({"start": segment["start"], "end": segment["end"]})
    return merged


def segments_to_schedule(segments: list[Segment], slots: list[PriceSlot]) -> list[dict[str, str | float]]:
    """Per-slot 0/1 view of the plan, aligned with the price list, for graphs."""
    return [
        {
            "start": slot.start.isoformat(),
            "value": 1.0 if any(seg["start"] < slot.end and seg["end"] > slot.start for seg in segments) else 0.0,
        }
        for slot in slots
    ]


def price_at(slots: list[PriceSlot], moment: datetime) -> float | None:
    """The price valid at ``moment``."""
    for slot in slots:
        if slot.start <= moment < slot.end:
            return slot.price
    return None
