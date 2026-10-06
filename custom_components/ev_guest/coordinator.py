"""Coordinator for EV Guest."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
import logging
from math import ceil
from typing import Any

from aiohttp import ClientSession
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_point_in_time, async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .api import (
    EVGuestAuthError,
    EVGuestLookupError,
    VehicleLookupResult,
    async_decode_vin_nhtsa,
    async_lookup_battery_open_ev_data,
    async_lookup_vehicle,
    async_validate_plate_provider_credentials,
    get_default_plate_provider,
)
from .const import (
    ATTR_CHARGING_SCHEDULE,
    ATTR_CHARGING_SEGMENTS,
    ATTR_COUNTRY,
    ATTR_FUEL_TYPE,
    ATTR_LAST_CALCULATION,
    ATTR_LAST_LOOKUP,
    ATTR_LAST_SOURCE,
    ATTR_MATCH_SCORE,
    ATTR_MODEL_YEAR,
    ATTR_PLAN_LOCKED,
    ATTR_PLAN_MODE,
    ATTR_PLATE_PROVIDER,
    ATTR_RAW_TWO_DAYS,
    ATTR_VIN,
    CONF_COUNTRY,
    CONF_CURRENCY,
    CONF_DURATION_FORMAT,
    CONF_MOTORAPI_KEY,
    CONF_PLATE_PROVIDER,
    CONF_PRICE_ENTITY,
    CONF_TIME_FORMAT,
    DEFAULT_COUNTRY,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    DURATION_FORMAT_HM,
    INPUT_BATTERY_CAPACITY,
    INPUT_CHARGE_COMPLETION_TIME,
    INPUT_CHARGE_LIMIT,
    INPUT_CHARGER_POWER,
    INPUT_CONTINUOUS_CHARGING_PREFERRED,
    INPUT_LICENSE_PLATE,
    INPUT_SOC,
    INPUT_USE_COMPLETION_TIME,
    RESULT_CAR_BATTERY_CAPACITY,
    RESULT_CAR_BRAND,
    RESULT_CAR_MODEL,
    RESULT_CAR_VARIANT,
    RESULT_CHARGE_COSTS,
    RESULT_CHARGE_END_TIME,
    RESULT_CHARGE_START_TIME,
    RESULT_CHARGE_TIME,
    RESULT_CHARGING_SPEED,
    RESULT_STATUS,
    STORAGE_KEY,
    STORAGE_VERSION,
    TIME_FORMAT_12H,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class EVGuestData:
    """Coordinator state."""

    inputs: dict[str, Any]
    results: dict[str, Any]
    service_health: dict[str, bool]


class EVGuestCoordinator(DataUpdateCoordinator[EVGuestData]):
    """Central state holder and calculator."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.hass = hass
        self.config_entry = entry
        self.session: ClientSession = async_get_clientsession(hass)
        self._remove_price_listener: CALLBACK_TYPE | None = None
        self._availability_logged: dict[str, bool] = {}
        self._boundary_callbacks: list[CALLBACK_TYPE] = []
        # Planned charging intervals as (start, end) datetimes. This is the
        # source of truth for charge_now; charging_schedule is hourly and only
        # meant for graphs.
        self._plan_segments: list[dict[str, datetime]] = []
        # Automatic recalculation on price updates is only allowed after the
        # user has requested a calculation, and only until the plan starts.
        self._auto_recalculate = False
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, STORAGE_KEY.format(entry_id=entry.entry_id)
        )
        self.data = EVGuestData(
            inputs={
                INPUT_LICENSE_PLATE: "",
                INPUT_SOC: 20.0,
                INPUT_BATTERY_CAPACITY: 77.0,
                INPUT_CHARGER_POWER: 11.0,
                INPUT_CHARGE_LIMIT: 80.0,
                INPUT_CHARGE_COMPLETION_TIME: "07:00",
                INPUT_USE_COMPLETION_TIME: True,
                INPUT_CONTINUOUS_CHARGING_PREFERRED: True,
            },
            results={
                RESULT_CHARGING_SPEED: None,
                RESULT_CHARGE_START_TIME: None,
                RESULT_CHARGE_END_TIME: None,
                RESULT_CHARGE_TIME: None,
                RESULT_CHARGE_COSTS: None,
                RESULT_CAR_BRAND: None,
                RESULT_CAR_MODEL: None,
                RESULT_CAR_VARIANT: None,
                RESULT_CAR_BATTERY_CAPACITY: None,
                RESULT_STATUS: "Ready",
                ATTR_LAST_LOOKUP: None,
                ATTR_LAST_CALCULATION: None,
                ATTR_LAST_SOURCE: None,
                ATTR_VIN: None,
                ATTR_MODEL_YEAR: None,
                ATTR_FUEL_TYPE: None,
                ATTR_MATCH_SCORE: None,
                ATTR_CHARGING_SCHEDULE: [],
                ATTR_RAW_TWO_DAYS: [],
                ATTR_PLAN_MODE: "continuous",
                ATTR_CHARGING_SEGMENTS: [],
                ATTR_COUNTRY: self.config.get(CONF_COUNTRY, DEFAULT_COUNTRY),
                ATTR_PLATE_PROVIDER: self.plate_provider,
            },
            service_health={"motorapi": True, "nhtsa": True, "open_ev_data": True},
        )

    @property
    def config(self) -> dict[str, Any]:
        return {**self.config_entry.data, **self.config_entry.options}

    @property
    def currency(self) -> str:
        return self.config.get(CONF_CURRENCY, "DKK")

    @property
    def country(self) -> str:
        return self.config.get(CONF_COUNTRY, DEFAULT_COUNTRY)

    @property
    def plate_provider(self) -> str:
        return self.config.get(CONF_PLATE_PROVIDER) or get_default_plate_provider(self.country)

    @property
    def has_motorapi_key(self) -> bool:
        return bool(str(self.config.get(CONF_MOTORAPI_KEY) or "").strip())

    async def async_initialize(self) -> None:
        await self._async_validate_setup()
        await self._async_load_state()
        parsed_time = self._parse_completion_time(self.data.inputs.get(INPUT_CHARGE_COMPLETION_TIME))
        if parsed_time is not None:
            self.data.inputs[INPUT_CHARGE_COMPLETION_TIME] = self._format_time_for_input(parsed_time)
        price_entity = self.config[CONF_PRICE_ENTITY]
        self._remove_price_listener = async_track_state_change_event(
            self.hass,
            [price_entity],
            self._handle_price_update,
        )
        self._schedule_plan_boundaries()
        await self.async_refresh()

    async def _async_validate_setup(self) -> None:
        """Validate the MotorAPI key, if one is configured.

        The plate lookup is optional: without a key EV Guest still works as a
        calculator. Connection problems never block setup, only an invalid key
        triggers reauthentication.
        """
        if not self.has_motorapi_key:
            return
        try:
            await async_validate_plate_provider_credentials(
                self.session,
                self.country,
                self.plate_provider,
                self.config[CONF_MOTORAPI_KEY],
            )
            self._set_service_health("motorapi", True)
        except EVGuestAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except EVGuestLookupError as err:
            if str(err) == "unsupported_provider":
                raise ConfigEntryError(str(err)) from err
            _LOGGER.warning("Could not validate MotorAPI key during setup: %s", err)
            self._set_service_health("motorapi", False)

    async def async_shutdown(self) -> None:
        if self._remove_price_listener:
            self._remove_price_listener()
            self._remove_price_listener = None
        self._cancel_plan_boundaries()

    @callback
    def _handle_price_update(self, event: Event) -> None:
        if not self._auto_recalculate or self.is_plan_locked():
            return
        self.hass.async_create_task(self.async_calculate(manual=False))

    async def _async_update_data(self) -> EVGuestData:
        self.data.results[ATTR_COUNTRY] = self.country
        self.data.results[ATTR_PLATE_PROVIDER] = self.plate_provider
        return self.data

    # ------------------------------------------------------------------
    # Persistence

    async def _async_load_state(self) -> None:
        stored = await self._store.async_load()
        if not isinstance(stored, dict):
            return
        for key, value in (stored.get("inputs") or {}).items():
            if key in self.data.inputs:
                self.data.inputs[key] = value
        for key, value in (stored.get("results") or {}).items():
            if key in self.data.results:
                self.data.results[key] = value
        self._plan_segments = self._parse_segments(stored.get("segments") or [])
        self._auto_recalculate = bool(stored.get("auto_recalculate", False))

    @callback
    def _async_save_state(self) -> None:
        self._store.async_delay_save(self._data_to_store, 1)

    @callback
    def _data_to_store(self) -> dict[str, Any]:
        return {
            "inputs": dict(self.data.inputs),
            "results": dict(self.data.results),
            "segments": self._serialize_segments(self._plan_segments),
            "auto_recalculate": self._auto_recalculate,
        }

    @staticmethod
    def _serialize_segments(segments: list[dict[str, datetime]]) -> list[dict[str, str]]:
        return [
            {"start": segment["start"].isoformat(), "end": segment["end"].isoformat()}
            for segment in segments
        ]

    @staticmethod
    def _parse_segments(raw: list[Any]) -> list[dict[str, datetime]]:
        segments: list[dict[str, datetime]] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            start = dt_util.parse_datetime(str(item.get("start", "")))
            end = dt_util.parse_datetime(str(item.get("end", "")))
            if start is None or end is None or end <= start:
                continue
            segments.append({"start": start, "end": end})
        return sorted(segments, key=lambda seg: seg["start"])

    async def async_set_input_value(self, key: str, value: Any) -> None:
        if key == INPUT_CHARGE_COMPLETION_TIME:
            parsed = self._parse_completion_time(value)
            if parsed is None:
                self.data.results[RESULT_STATUS] = "Invalid completion time"
                self.async_update_listeners()
                return
            value = self._format_time_for_input(parsed)
        self.data.inputs[key] = value
        self._async_save_state()
        self.async_update_listeners()

    def get_completion_time_text(self) -> str:
        parsed = self._parse_completion_time(self.data.inputs.get(INPUT_CHARGE_COMPLETION_TIME, "07:00"))
        return self._format_time_for_input(parsed or time(hour=7, minute=0))

    def _format_time_for_input(self, value: time) -> str:
        if self.config.get(CONF_TIME_FORMAT) == TIME_FORMAT_12H:
            return value.strftime("%I:%M %p").lstrip("0")
        return value.strftime("%H:%M")

    def _parse_completion_time(self, value: Any) -> time | None:
        if isinstance(value, time):
            return value
        if value is None:
            return None
        text = str(value).strip()
        for fmt in ("%H:%M", "%I:%M %p", "%I:%M%p"):
            try:
                return datetime.strptime(text, fmt).time()
            except ValueError:
                continue
        return None

    def _set_service_health(self, service: str, available: bool) -> None:
        current = self.data.service_health.get(service)
        self.data.service_health[service] = available
        if current is None or current == available:
            return
        if not available and not self._availability_logged.get(service, False):
            _LOGGER.warning("%s is unavailable", service)
            self._availability_logged[service] = True
        elif available and self._availability_logged.get(service, False):
            _LOGGER.info("%s is available again", service)
            self._availability_logged[service] = False

    async def async_lookup_car_data(self) -> None:
        plate = self.data.inputs.get(INPUT_LICENSE_PLATE, "")
        if not plate:
            self.data.results[RESULT_STATUS] = "License plate is required"
            self.async_update_listeners()
            return
        if not self.has_motorapi_key:
            self.data.results[RESULT_STATUS] = "MotorAPI API key not configured - enter battery capacity manually"
            self.async_update_listeners()
            return

        try:
            motor = await async_lookup_vehicle(
                self.session,
                plate,
                self.config[CONF_MOTORAPI_KEY],
                self.country,
                self.plate_provider,
            )
            self._set_service_health("motorapi", True)
        except EVGuestAuthError:
            self._set_service_health("motorapi", False)
            self.data.results[RESULT_STATUS] = "Invalid MotorAPI API key"
            self.config_entry.async_start_reauth(self.hass)
            self.async_update_listeners()
            return
        except EVGuestLookupError as err:
            self._set_service_health("motorapi", False if str(err) in {"cannot_connect", "timeout"} else True)
            self.data.results[RESULT_STATUS] = f"Lookup failed: {err}"
            self.async_update_listeners()
            return

        decoded = None
        if motor.vin:
            decoded = await async_decode_vin_nhtsa(self.session, motor.vin, motor.model_year)
            self._set_service_health("nhtsa", decoded is not None)
        else:
            self._set_service_health("nhtsa", True)

        normalized = self._merge_vehicle_results(motor, decoded)
        battery = await async_lookup_battery_open_ev_data(
            self.session,
            normalized.brand,
            normalized.model,
            normalized.variant,
            normalized.model_year,
        )
        self._set_service_health("open_ev_data", battery.raw is not None or battery.battery_capacity is None)

        self.data.results.update(
            {
                RESULT_CAR_BRAND: normalized.brand,
                RESULT_CAR_MODEL: normalized.model,
                RESULT_CAR_VARIANT: normalized.variant,
                RESULT_CAR_BATTERY_CAPACITY: battery.battery_capacity,
                ATTR_VIN: normalized.vin,
                ATTR_MODEL_YEAR: normalized.model_year,
                ATTR_FUEL_TYPE: normalized.fuel_type,
                ATTR_MATCH_SCORE: battery.match_score,
                ATTR_LAST_SOURCE: f"{normalized.source} + {battery.source}",
                ATTR_LAST_LOOKUP: self._local_now().isoformat(),
            }
        )
        if battery.battery_capacity:
            self.data.inputs[INPUT_BATTERY_CAPACITY] = battery.battery_capacity
        self.data.results[RESULT_STATUS] = "Car data updated"
        self._async_save_state()
        self.async_update_listeners()

    def _merge_vehicle_results(
        self,
        primary: VehicleLookupResult,
        fallback: VehicleLookupResult | None,
    ) -> VehicleLookupResult:
        return VehicleLookupResult(
            plate=primary.plate,
            vin=primary.vin or (fallback.vin if fallback else None),
            brand=primary.brand or (fallback.brand if fallback else None),
            model=primary.model or (fallback.model if fallback else None),
            variant=primary.variant or (fallback.variant if fallback else None),
            model_year=primary.model_year or (fallback.model_year if fallback else None),
            fuel_type=primary.fuel_type or (fallback.fuel_type if fallback else None),
            source=primary.source,
            raw=primary.raw,
        )

    async def async_calculate(self, manual: bool = True) -> None:
        """Calculate the cheapest charging plan.

        EV Guest only knows the SoC at the time of calculation, it never sees
        the car's live SoC. A plan is therefore locked once it has started:
        automatic recalculations (price updates) are skipped from then on, so
        a static start SoC can never make the plan slide or repeat. Pressing
        Calculate always makes a fresh plan.
        """
        if manual:
            self._auto_recalculate = True
        elif self.is_plan_locked():
            return

        try:
            calculation = self._calculate_schedule()
        except ValueError as err:
            self.data.results[RESULT_STATUS] = str(err)
            if manual:
                # Do not keep following an old plan the user tried to replace.
                self._set_plan([])
            self._async_save_state()
            self.async_update_listeners()
            return

        segments = calculation.pop("plan_segments")
        self.data.results.update(calculation)
        self.data.results[ATTR_LAST_CALCULATION] = self._local_now().isoformat()
        self.data.results[RESULT_STATUS] = "Calculation ready"
        self._set_plan(segments)
        self._async_save_state()
        self.async_update_listeners()

    def _calculate_schedule(self) -> dict[str, Any]:
        soc = float(self.data.inputs[INPUT_SOC])
        battery_capacity = float(self.data.inputs[INPUT_BATTERY_CAPACITY])
        charger_power = float(self.data.inputs[INPUT_CHARGER_POWER])
        charge_limit = float(self.data.inputs[INPUT_CHARGE_LIMIT])
        use_completion_time = bool(self.data.inputs.get(INPUT_USE_COMPLETION_TIME, True))
        completion_time = self._parse_completion_time(self.data.inputs.get(INPUT_CHARGE_COMPLETION_TIME))
        continuous = bool(self.data.inputs.get(INPUT_CONTINUOUS_CHARGING_PREFERRED, True))

        if battery_capacity <= 0:
            raise ValueError("Battery capacity must be above 0")
        if charger_power <= 0:
            raise ValueError("Charger power must be above 0")
        if not 0 <= soc <= 100:
            raise ValueError("SoC must be between 0 and 100")
        if not 0 <= charge_limit <= 100:
            raise ValueError("Charge limit must be between 0 and 100")
        if charge_limit <= soc:
            raise ValueError("Charge limit must be above current SoC")
        if use_completion_time and completion_time is None:
            raise ValueError("Completion time is invalid")

        speed_pct_per_hour = (charger_power / battery_capacity) * 100
        energy_needed_kwh = battery_capacity * ((charge_limit - soc) / 100)
        charge_minutes = ceil((energy_needed_kwh / charger_power) * 60)
        required_hours = charge_minutes / 60
        hours_needed = ceil(required_hours)

        prices = self._extract_price_slots()
        if not prices:
            raise ValueError("No usable price data available from selected price sensor")

        visible_prices = prices[:48]
        self.data.results[ATTR_RAW_TWO_DAYS] = [
            {"start": dt.isoformat(), "value": price} for dt, price in visible_prices
        ]

        now = self._local_now()
        planning_prices = prices if use_completion_time else visible_prices
        valid_prices = [slot for slot in planning_prices if now <= slot[0]]
        completion_dt = None
        if use_completion_time:
            completion_dt = self._next_completion_datetime(now, completion_time)
            valid_prices = [slot for slot in valid_prices if slot[0] < completion_dt]
            if len(valid_prices) < hours_needed:
                raise ValueError("Not enough future hourly prices available before completion time")
        if len(valid_prices) < hours_needed:
            raise ValueError("Not enough future hourly prices available")

        if continuous:
            plan_segments, plan_cost = self._select_continuous_segments(
                valid_prices, energy_needed_kwh, required_hours, charge_minutes, completion_dt
            )
            mode = "continuous"
        else:
            plan_segments, plan_cost = self._select_discrete_segments(
                valid_prices, energy_needed_kwh, required_hours, charge_minutes, completion_dt
            )
            mode = "split"

        if not plan_segments:
            raise ValueError("No valid charging window found")

        self.data.results[ATTR_CHARGING_SCHEDULE] = self._segments_to_schedule(plan_segments, visible_prices)
        self.data.results[ATTR_PLAN_MODE] = mode
        self.data.results[ATTR_COUNTRY] = self.country
        self.data.results[ATTR_PLATE_PROVIDER] = self.plate_provider

        start = min(segment["start"] for segment in plan_segments)
        end = max(segment["end"] for segment in plan_segments)

        return {
            RESULT_CHARGING_SPEED: round(speed_pct_per_hour, 1),
            RESULT_CHARGE_START_TIME: self._format_datetime(start),
            RESULT_CHARGE_END_TIME: self._format_datetime(end),
            RESULT_CHARGE_TIME: self._format_duration(charge_minutes),
            RESULT_CHARGE_COSTS: round(plan_cost, 2),
            "plan_segments": plan_segments,
        }

    def _extract_price_slots(self) -> list[tuple[datetime, float]]:
        state = self.hass.states.get(self.config[CONF_PRICE_ENTITY])
        if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return []

        slots: list[tuple[datetime, float]] = []
        attrs = state.attributes

        for key in ("raw_today", "raw_tomorrow", "forecast"):
            for row in (attrs.get(key) or []):
                if isinstance(row, dict) and row.get("hour") is not None and row.get("price") is not None:
                    dt = dt_util.parse_datetime(str(row["hour"]))
                    if dt is not None:
                        slots.append((dt, float(row["price"])))

        if not slots and isinstance(attrs.get("today"), list):
            base = self._local_now().replace(hour=0, minute=0, second=0, microsecond=0)
            for idx, price in enumerate(attrs["today"]):
                slots.append((base + timedelta(hours=idx), float(price)))
            if isinstance(attrs.get("tomorrow"), list):
                next_base = base + timedelta(days=1)
                for idx, price in enumerate(attrs["tomorrow"]):
                    slots.append((next_base + timedelta(hours=idx), float(price)))

        deduped: dict[str, tuple[datetime, float]] = {}
        for dt, price in slots:
            deduped[dt.isoformat()] = (dt, price)
        return [deduped[key] for key in sorted(deduped.keys())]

    def _select_continuous_segments(
        self,
        valid_prices: list[tuple[datetime, float]],
        energy_needed_kwh: float,
        required_hours: float,
        charge_minutes: int,
        completion_dt: datetime | None,
    ) -> tuple[list[dict[str, Any]], float]:
        hours_needed = ceil(required_hours)
        cheapest_window = None
        for index in range(0, len(valid_prices) - hours_needed + 1):
            window = valid_prices[index : index + hours_needed]
            if completion_dt and window[-1][0] + timedelta(hours=1) > completion_dt:
                continue
            cost = self._window_cost(window, energy_needed_kwh, required_hours)
            if cheapest_window is None or cost < cheapest_window["cost"]:
                cheapest_window = {
                    "window": window,
                    "cost": cost,
                }

        if cheapest_window is None:
            return [], 0.0

        start = cheapest_window["window"][0][0]
        end = start + timedelta(minutes=charge_minutes)
        return ([{"start": start, "end": end}], cheapest_window["cost"])

    def _select_discrete_segments(
        self,
        valid_prices: list[tuple[datetime, float]],
        energy_needed_kwh: float,
        required_hours: float,
        charge_minutes: int,
        completion_dt: datetime | None,
    ) -> tuple[list[dict[str, Any]], float]:
        """Pick the cheapest hours, not necessarily adjacent.

        Full hours go to the cheapest slots. A remaining partial hour goes to
        the next-cheapest slot (the most expensive one chosen), which is the
        cheapest possible split. Slots must end before the completion time.
        """
        candidates = valid_prices
        if completion_dt:
            candidates = [slot for slot in valid_prices if slot[0] + timedelta(hours=1) <= completion_dt]

        hours_needed = ceil(required_hours)
        if len(candidates) < hours_needed:
            return [], 0.0

        by_price = sorted(candidates, key=lambda item: (item[1], item[0]))[:hours_needed]
        full_hours = int(required_hours)
        fraction = required_hours - full_hours
        energy_per_hour = energy_needed_kwh / required_hours

        full_slots = by_price[:full_hours]
        full_starts = {start for start, _price in full_slots}
        total_cost = 0.0
        segments: list[dict[str, Any]] = []
        for start, price in full_slots:
            segments.append({"start": start, "end": start + timedelta(hours=1)})
            total_cost += price * energy_per_hour

        if fraction > 1e-9:
            start, price = by_price[full_hours]
            duration = timedelta(hours=fraction)
            slot_end = start + timedelta(hours=1)
            if slot_end in full_starts:
                # Place the partial charge at the end of its hour so it joins
                # the following charging hour instead of leaving a gap.
                segments.append({"start": slot_end - duration, "end": slot_end})
            else:
                segments.append({"start": start, "end": start + duration})
            total_cost += price * energy_per_hour * fraction

        return self._merge_segments(segments), total_cost

    @staticmethod
    def _merge_segments(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        for segment in sorted(segments, key=lambda seg: seg["start"]):
            if merged and segment["start"] <= merged[-1]["end"]:
                merged[-1]["end"] = max(merged[-1]["end"], segment["end"])
            else:
                merged.append({"start": segment["start"], "end": segment["end"]})
        return merged

    def _segments_to_schedule(
        self,
        plan_segments: list[dict[str, Any]],
        price_slots: list[tuple[datetime, float]],
    ) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        for start, _price in price_slots:
            end = start + timedelta(hours=1)
            value = 0.0
            for segment in plan_segments:
                if segment["start"] < end and segment["end"] > start:
                    value = 1.0
                    break
            output.append({"start": start.isoformat(), "value": value})
        return output

    def _window_cost(self, window: list[tuple[datetime, float]], energy_needed_kwh: float, required_hours: float) -> float:
        if not window:
            return 0.0
        energy_per_hour = energy_needed_kwh / required_hours
        remaining = required_hours
        total = 0.0
        for _, price in window:
            if remaining <= 0:
                break
            fraction = min(1.0, remaining)
            total += price * energy_per_hour * fraction
            remaining -= fraction
        return total

    # ------------------------------------------------------------------
    # Plan state and charge_now

    @callback
    def _set_plan(self, segments: list[dict[str, Any]]) -> None:
        self._plan_segments = [{"start": seg["start"], "end": seg["end"]} for seg in segments]
        self.data.results[ATTR_CHARGING_SEGMENTS] = self._serialize_segments(self._plan_segments)
        if not segments:
            self.data.results[ATTR_CHARGING_SCHEDULE] = []
        self._schedule_plan_boundaries()

    @callback
    def _schedule_plan_boundaries(self) -> None:
        """Push a state update exactly when charge_now should change."""
        self._cancel_plan_boundaries()
        now = self._local_now()
        for segment in self._plan_segments:
            for moment in (segment["start"], segment["end"]):
                if moment > now:
                    self._boundary_callbacks.append(
                        async_track_point_in_time(self.hass, self._handle_plan_boundary, moment)
                    )

    @callback
    def _cancel_plan_boundaries(self) -> None:
        while self._boundary_callbacks:
            remove = self._boundary_callbacks.pop()
            remove()

    @callback
    def _handle_plan_boundary(self, _now: datetime) -> None:
        self.async_update_listeners()

    def is_plan_locked(self, now: datetime | None = None) -> bool:
        """True once the current plan has started (also after it has finished)."""
        if not self._plan_segments:
            return False
        now = now or self._local_now()
        return self._plan_segments[0]["start"] <= now

    def is_charge_now(self, now: datetime | None = None) -> bool:
        now = now or self._local_now()
        return any(segment["start"] <= now < segment["end"] for segment in self._plan_segments)

    def _local_now(self) -> datetime:
        return dt_util.now()

    def _next_completion_datetime(self, now: datetime, completion: time) -> datetime:
        dt = now.replace(hour=completion.hour, minute=completion.minute, second=0, microsecond=0)
        if dt <= now:
            dt += timedelta(days=1)
        return dt

    def _format_datetime(self, value: datetime) -> str:
        if self.config.get(CONF_TIME_FORMAT) == TIME_FORMAT_12H:
            return value.strftime("%I:%M %p").lstrip("0")
        return value.strftime("%H:%M")

    def _format_duration(self, minutes: int) -> str | int:
        if self.config.get(CONF_DURATION_FORMAT) == DURATION_FORMAT_HM:
            hours, rem = divmod(minutes, 60)
            return f"{hours}h {rem}m"
        return minutes
