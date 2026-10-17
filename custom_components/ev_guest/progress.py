"""How far a charging plan has come, without seeing the car.

Pure Python without Home Assistant imports. EV Guest never sees a guest
car's live charge level, so the charge level is estimated:

* from the plan: the charging time that has passed at the charger power,
  less charging losses. This works without any extra hardware.
* from an energy meter, when one is set: the energy the charger actually
  delivered, less charging losses.

Comparing the two shows a car that charges slower than planned.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from .planner import Segment

SOURCE_PLAN = "plan"
SOURCE_METER = "meter"

# A car is behind its plan when the meter has counted less than this share of
# the energy planned so far ...
BEHIND_PLAN_RATIO = 0.8
# ... and at least this much less, so small plans and rounding never count ...
BEHIND_PLAN_MIN_KWH = 1.0
# ... after at least this much planned charging, so a slow start or a meter
# that reports in steps is not flagged.
BEHIND_PLAN_MIN_CHARGING = timedelta(minutes=20)


@dataclass(frozen=True, slots=True)
class Progress:
    """The estimated state of a plan at one moment."""

    start_soc: float
    """The charge level the plan was made from (%)."""
    target_soc: float
    """The charge level the plan aims for (%)."""
    planned_soc: float
    """The charge level the plan expects by now (%)."""
    planned_energy: float
    """Energy from the grid the plan expects by now (kWh)."""
    charged: timedelta
    """Planned charging time that has passed."""
    measured_soc: float | None = None
    """The charge level from the energy meter (%), when there is one."""
    measured_energy: float | None = None
    """Energy from the grid the meter has counted (kWh), when there is one."""

    @property
    def source(self) -> str:
        return SOURCE_PLAN if self.measured_soc is None else SOURCE_METER

    @property
    def soc(self) -> float:
        """The best estimate of the charge level now (%)."""
        return self.planned_soc if self.measured_soc is None else self.measured_soc

    @property
    def behind_plan(self) -> bool | None:
        """Whether the charger delivers clearly less than planned.

        None without an energy meter: then there is nothing to compare with.
        """
        if self.measured_energy is None:
            return None
        if self.charged < BEHIND_PLAN_MIN_CHARGING:
            return False
        missing = self.planned_energy - self.measured_energy
        return self.measured_energy < self.planned_energy * BEHIND_PLAN_RATIO and missing >= BEHIND_PLAN_MIN_KWH


def charged_time(segments: Sequence[Segment], now: datetime) -> timedelta:
    """The part of the planned charging time that lies before ``now``."""
    total = timedelta()
    for segment in segments:
        if segment["start"] >= now:
            continue
        total += min(now, segment["end"]) - segment["start"]
    return total


def plan_progress(
    segments: Sequence[Segment],
    plan_inputs: Mapping[str, Any] | None,
    now: datetime,
    measured_energy: float | None = None,
) -> Progress | None:
    """Estimate the charge level of the plan's car at ``now``.

    ``plan_inputs`` are the inputs the plan was made with (SoC, limit,
    battery capacity, charger power and efficiency). Returns None without a
    plan, or when the plan's inputs are unknown or unusable.
    """
    if not segments or not plan_inputs:
        return None
    try:
        start_soc = float(plan_inputs["soc"])
        target_soc = float(plan_inputs["charge_limit"])
        capacity = float(plan_inputs["battery_capacity"])
        power = float(plan_inputs["charger_power"])
        efficiency = float(plan_inputs.get("charging_efficiency") or 100) / 100
    except (KeyError, TypeError, ValueError):
        return None
    if capacity <= 0 or power <= 0 or efficiency <= 0:
        return None

    charged = charged_time(segments, now)
    planned_energy = power * charged.total_seconds() / 3600
    planned_soc = min(target_soc, start_soc + planned_energy * efficiency / capacity * 100)

    measured_soc = None
    if measured_energy is not None:
        measured_soc = min(100.0, start_soc + max(0.0, measured_energy) * efficiency / capacity * 100)

    return Progress(
        start_soc=start_soc,
        target_soc=target_soc,
        planned_soc=max(start_soc, planned_soc),
        planned_energy=planned_energy,
        charged=charged,
        measured_soc=measured_soc,
        measured_energy=measured_energy,
    )
