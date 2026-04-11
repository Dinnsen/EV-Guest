"""Coordinator and planner for EV Guest."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from json import JSONDecodeError, loads as json_loads
import logging
from math import ceil
from typing import Any

from aiohttp import ClientSession
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError, HomeAssistantError
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.event import (
    async_track_point_in_time,
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .api import (
    EVGuestAuthError,
    EVGuestLookupError,
    async_decode_vin_nhtsa,
    async_lookup_battery_open_ev_data,
    async_lookup_vehicle_by_country,
    async_validate_country_provider_credentials,
    get_default_plate_provider,
)
from .const import (
    ATTR_CHARGER_BACKEND,
    ATTR_CHARGER_COMMANDABLE,
    ATTR_CHARGER_CONTROL_ENABLED,
    ATTR_CHARGER_ENTITY,
    ATTR_CHARGER_EXPECTED_ON,
    ATTR_CHARGER_MISMATCH,
    ATTR_CHARGER_STATUS_ENTITY,
    ATTR_CHARGING_SCHEDULE,
    ATTR_CONTROL_TICK_INTERVAL,
    ATTR_DUMMY_CHARGER,
    ATTR_FUEL_TYPE,
    ATTR_LAST_CALCULATION,
    ATTR_LAST_LOOKUP,
    ATTR_LAST_SOURCE,
    ATTR_LAST_CHARGER_COMMAND_AT,
    ATTR_LAST_CHARGER_COMMAND_REASON,
    ATTR_LANGUAGE,
    ATTR_COUNTRY,
    ATTR_PLATE_PROVIDER,
    ATTR_MATCH_SCORE,
    ATTR_MODEL_YEAR,
    ATTR_PLAN_MODE,
    ATTR_RAW_TWO_DAYS,
    ATTR_VIN,
    CHARGER_BACKEND_DUMMY,
    CHARGER_BACKEND_GENERIC,
    CONF_CHARGER_BACKEND,
    CONF_CHARGER_START_DATA,
    CONF_CHARGER_START_SERVICE,
    CONF_CHARGER_STATUS_ENTITY,
    CONF_CHARGER_STOP_DATA,
    CONF_CHARGER_STOP_SERVICE,
    CONF_CHARGER_SWITCH_ENTITY,
    CONF_COUNTRY,
    CONF_CURRENCY,
    CONF_LANGUAGE,
    CONF_DURATION_FORMAT,
    CONF_MOTORAPI_KEY,
    CONF_PRICE_ENTITY,
    CONF_TIME_FORMAT,
    CONTROL_VERIFY_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    DURATION_FORMAT_HM,
    INPUT_BATTERY_CAPACITY,
    INPUT_CHARGE_COMPLETION_TIME,
    INPUT_CHARGE_LIMIT,
    INPUT_CHARGER_POWER,
    INPUT_CONTINUOUS_CHARGING_PREFERRED,
    INPUT_ENABLE_CHARGER_CONTROL,
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
    RESULT_CHARGER_ACTIVE_WINDOW,
    RESULT_CHARGER_ACTUAL_STATE,
    RESULT_CHARGER_BACKEND,
    RESULT_CHARGER_LAST_COMMAND,
    RESULT_CHARGER_LAST_RESULT,
    RESULT_CHARGER_NEXT_START,
    RESULT_CHARGER_NEXT_STOP,
    RESULT_CHARGER_TARGET_STATE,
    RESULT_CHARGING_SPEED,
    RESULT_STATUS,
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
        self.config = {**entry.data, **entry.options}
        self.session: ClientSession = aiohttp_client.async_get_clientsession(hass)
        self._remove_price_listener = None
        self._remove_control_tick = None
        self._scheduled_callbacks: list[callable] = []
        self._availability_logged: dict[str, bool] = {}
        self._plan_segments: list[dict[str, Any]] = []
        self._dummy_charger_on = False
        self.data = EVGuestData(
            inputs={
                INPUT_LICENSE_PLATE: "",
                INPUT_SOC: 20,
                INPUT_BATTERY_CAPACITY: 60.0,
                INPUT_CHARGER_POWER: 11.0,
                INPUT_CHARGE_LIMIT: 80,
                INPUT_CHARGE_COMPLETION_TIME: "07:00",
                INPUT_USE_COMPLETION_TIME: True,
                INPUT_ENABLE_CHARGER_CONTROL: False,
                INPUT_CONTINUOUS_CHARGING_PREFERRED: True,
            },
            results={
                RESULT_STATUS: "Ready",
                RESULT_CHARGER_BACKEND: self.charger_backend,
                RESULT_CHARGER_TARGET_STATE: "unknown",
                RESULT_CHARGER_ACTUAL_STATE: "unknown",
                RESULT_CHARGER_LAST_COMMAND: "none",
                RESULT_CHARGER_LAST_RESULT: "idle",
                RESULT_CHARGER_NEXT_START: None,
                RESULT_CHARGER_NEXT_STOP: None,
                RESULT_CHARGER_ACTIVE_WINDOW: None,
                ATTR_CONTROL_TICK_INTERVAL: str(CONTROL_VERIFY_INTERVAL),
                ATTR_LANGUAGE: self.language,
                ATTR_COUNTRY: self.country,
                ATTR_PLATE_PROVIDER: self.plate_provider,
            },
            service_health={"plate_provider": True},
        )

    @property
    def currency(self) -> str:
        return self.config.get(CONF_CURRENCY, "DKK")

    @property
    def language(self) -> str:
        return self.config.get(CONF_LANGUAGE, "en")

    @property
    def country(self) -> str:
        return self.config.get(CONF_COUNTRY, "dk")

    @property
    def plate_provider(self) -> str:
        return get_default_plate_provider(self.country)

    @property
    def charger_backend(self) -> str:
        return self.config.get(CONF_CHARGER_BACKEND, CHARGER_BACKEND_GENERIC)

    @property
    def uses_dummy_backend(self) -> bool:
        return self.charger_backend == CHARGER_BACKEND_DUMMY

    @property
    def dummy_charger_on(self) -> bool:
        return self._dummy_charger_on

    @property
    def debug_plan_segments(self) -> list[dict[str, Any]]:
        return [
            {
                "start": segment["start"].isoformat(),
                "end": segment["end"].isoformat(),
                "value": segment.get("value", 1.0),
            }
            for segment in self._plan_segments
        ]

    @property
    def is_planned_active_now(self) -> bool:
        now = self._local_now()
        return any(segment["start"] <= now < segment["end"] for segment in self._plan_segments)

    @property
    def expected_charger_on(self) -> bool:
        return self.is_planned_active_now and bool(
            self.data.inputs.get(INPUT_ENABLE_CHARGER_CONTROL, False)
        )

    @property
    def actual_charger_on(self) -> bool | None:
        return self._read_actual_charger_state()

    @property
    def charger_state_mismatch(self) -> bool:
        actual = self.actual_charger_on
        return actual is not None and actual != self.expected_charger_on

    @property
    def is_charger_commandable(self) -> bool:
        if self.uses_dummy_backend:
            return True
        if self.config.get(CONF_CHARGER_START_SERVICE) and self.config.get(CONF_CHARGER_STOP_SERVICE):
            return True
        return bool(self.config.get(CONF_CHARGER_SWITCH_ENTITY))

    async def async_initialize(self) -> None:
        await self._async_validate_setup()
        price_entity = self.config[CONF_PRICE_ENTITY]
        self._remove_price_listener = async_track_state_change_event(
            self.hass,
            [price_entity],
            self._handle_price_update,
        )
        self._remove_control_tick = async_track_time_interval(
            self.hass,
            self._handle_control_tick,
            CONTROL_VERIFY_INTERVAL,
        )
        await self.async_calculate()
        await self.async_refresh()

    async def _async_validate_setup(self) -> None:
        try:
            await async_validate_country_provider_credentials(self.session, self.country, self.config[CONF_MOTORAPI_KEY])
            self._set_service_health("plate_provider", True)
        except EVGuestAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except EVGuestLookupError as err:
            raise ConfigEntryError(str(err)) from err

    async def async_shutdown(self) -> None:
        if self._remove_price_listener:
            self._remove_price_listener()
        self._remove_price_listener = None
        if self._remove_control_tick:
            self._remove_control_tick()
        self._remove_control_tick = None
        self._cancel_scheduled_actions()

    @callback
    def _handle_price_update(self, event: Event) -> None:
        self.hass.async_create_task(self.async_calculate())

    @callback
    def _handle_control_tick(self, _now: datetime) -> None:
        self.hass.async_create_task(self._async_reconcile_charger_state("control_tick"))

    async def _async_update_data(self) -> EVGuestData:
        return self.data

    async def async_set_input_value(self, key: str, value: Any) -> None:
        if key == INPUT_CHARGE_COMPLETION_TIME:
            parsed = self._parse_completion_time(value)
            if parsed is None:
                self.data.results[RESULT_STATUS] = "Invalid completion time"
                self.async_update_listeners()
                return
            value = self._format_time_for_input(parsed)
        self.data.inputs[key] = value
        self._update_charger_diagnostics()
        self.async_update_listeners()

    def get_completion_time_text(self) -> str:
        parsed = self._parse_completion_time(
            self.data.inputs.get(INPUT_CHARGE_COMPLETION_TIME, "07:00")
        )
        return self._format_time_for_input(parsed or time(hour=7, minute=0))

    def _format_time_for_input(self, value: time) -> str:
        return value.strftime("%H:%M")

    def _parse_completion_time(self, value: Any) -> time | None:
        if isinstance(value, time):
            return value
        if isinstance(value, str):
            try:
                hours, minutes = value.strip().split(":", 1)
                return time(hour=int(hours), minute=int(minutes))
            except (TypeError, ValueError):
                return None
        return None

    def _set_service_health(self, service: str, healthy: bool) -> None:
        self.data.service_health[service] = healthy
        if healthy:
            self._availability_logged[service] = False
        elif not self._availability_logged.get(service):
            _LOGGER.warning("EV Guest upstream service unavailable: %s", service)
            self._availability_logged[service] = True

    async def async_lookup_car_data(self) -> None:
        plate = (self.data.inputs.get(INPUT_LICENSE_PLATE, "") or "").strip()
        if not plate:
            self.data.results[RESULT_STATUS] = "License plate is required"
            self.async_update_listeners()
            return

        try:
            motor = await async_lookup_vehicle_by_country(
                self.session, plate, self.country, self.config[CONF_MOTORAPI_KEY]
            )
            self._set_service_health("plate_provider", True)
        except EVGuestAuthError as err:
            self._set_service_health("plate_provider", False)
            self.data.results[RESULT_STATUS] = str(err)
            self.async_update_listeners()
            return
        except EVGuestLookupError as err:
            self._set_service_health("plate_provider", False)
            self.data.results[RESULT_STATUS] = str(err)
            self.async_update_listeners()
            return

        nhtsa = None
        if motor.vin:
            try:
                nhtsa = await async_decode_vin_nhtsa(self.session, motor.vin, motor.model_year)
            except EVGuestLookupError:
                nhtsa = None

        battery = await async_lookup_battery_open_ev_data(
            self.session,
            motor.brand or (nhtsa.brand if nhtsa else None),
            motor.model or (nhtsa.model if nhtsa else None),
            motor.variant or (nhtsa.variant if nhtsa else None),
            motor.model_year or (nhtsa.model_year if nhtsa else None),
        )

        self.data.results.update(
            {
                RESULT_CAR_BRAND: motor.brand or (nhtsa.brand if nhtsa else None),
                RESULT_CAR_MODEL: motor.model or (nhtsa.model if nhtsa else None),
                RESULT_CAR_VARIANT: motor.variant or (nhtsa.variant if nhtsa else None),
                RESULT_CAR_BATTERY_CAPACITY: battery.battery_capacity,
                ATTR_LAST_LOOKUP: self._local_now().isoformat(),
                ATTR_LAST_SOURCE: motor.source,
                ATTR_VIN: motor.vin,
                ATTR_MODEL_YEAR: motor.model_year or (nhtsa.model_year if nhtsa else None),
                ATTR_FUEL_TYPE: motor.fuel_type or (nhtsa.fuel_type if nhtsa else None),
                ATTR_MATCH_SCORE: battery.match_score,
                RESULT_STATUS: "Car data ready",
            }
        )
        if battery.battery_capacity:
            self.data.inputs[INPUT_BATTERY_CAPACITY] = battery.battery_capacity
        self.async_update_listeners()

    async def async_calculate(self) -> None:
        try:
            calculation = self._calculate_schedule()
        except ValueError as err:
            self.data.results[RESULT_STATUS] = str(err)
            self.async_update_listeners()
            return

        self.data.results.update(calculation)
        self.data.results[ATTR_LAST_CALCULATION] = self._local_now().isoformat()
        self.data.results[RESULT_STATUS] = "Calculation ready"
        self._plan_segments = calculation["plan_segments"]
        await self._async_apply_charger_plan(self._plan_segments)
        self._update_charger_diagnostics()
        self.async_update_listeners()

    async def async_force_start_charger(self) -> None:
        await self._async_set_charger_state(True, reason="manual_force_start")
        self._update_charger_diagnostics()
        self.async_update_listeners()

    async def async_force_stop_charger(self) -> None:
        await self._async_set_charger_state(False, reason="manual_force_stop")
        self._update_charger_diagnostics()
        self.async_update_listeners()

    async def async_resync_charger_plan(self) -> None:
        await self._async_apply_charger_plan(self._plan_segments)
        self._update_charger_diagnostics()
        self.async_update_listeners()

    async def async_set_dummy_charger_state(self, is_on: bool, reason: str) -> None:
        self._dummy_charger_on = is_on
        now = self._local_now().isoformat()
        self.data.results[RESULT_CHARGER_LAST_COMMAND] = "turn_on" if is_on else "turn_off"
        self.data.results[RESULT_CHARGER_LAST_RESULT] = f"dummy_ok ({reason})"
        self.data.results[ATTR_LAST_CHARGER_COMMAND_AT] = now
        self.data.results[ATTR_LAST_CHARGER_COMMAND_REASON] = reason
        self._update_charger_diagnostics()
        self.async_update_listeners()

    async def async_reset_dummy_charger(self) -> None:
        self._dummy_charger_on = False
        self.data.results[RESULT_CHARGER_LAST_RESULT] = "dummy_reset"
        self._update_charger_diagnostics()
        self.async_update_listeners()

    def _calculate_schedule(self) -> dict[str, Any]:
        soc = float(self.data.inputs.get(INPUT_SOC, 0) or 0)
        capacity = float(
            self.data.inputs.get(INPUT_BATTERY_CAPACITY)
            or self.data.results.get(RESULT_CAR_BATTERY_CAPACITY)
            or 0
        )
        power = float(self.data.inputs.get(INPUT_CHARGER_POWER, 0) or 0)
        limit = float(self.data.inputs.get(INPUT_CHARGE_LIMIT, 0) or 0)
        use_completion = bool(self.data.inputs.get(INPUT_USE_COMPLETION_TIME, True))
        completion_value = self._parse_completion_time(
            self.data.inputs.get(INPUT_CHARGE_COMPLETION_TIME, "07:00")
        )
        if capacity <= 0:
            raise ValueError("Battery capacity must be above 0")
        if power <= 0:
            raise ValueError("Charger power must be above 0")
        if limit <= soc:
            raise ValueError("Charge limit must be higher than current SoC")

        energy_needed_kwh = capacity * ((limit - soc) / 100)
        required_hours = energy_needed_kwh / power
        charge_minutes = ceil(required_hours * 60)

        price_slots = self._extract_price_slots()
        if not price_slots:
            raise ValueError("No usable electricity prices available")

        now = self._local_now()
        completion_dt = (
            self._next_completion_datetime(now, completion_value)
            if use_completion and completion_value
            else None
        )
        valid_prices = [
            (start, price)
            for start, price in price_slots
            if start + timedelta(hours=1) > now
            and (completion_dt is None or start < completion_dt)
        ]
        if not valid_prices:
            raise ValueError("No valid prices available before completion time")

        continuous = bool(
            self.data.inputs.get(INPUT_CONTINUOUS_CHARGING_PREFERRED, True)
        )
        if continuous:
            plan_segments, total_cost = self._select_continuous_segment(
                valid_prices, energy_needed_kwh, required_hours, charge_minutes, completion_dt
            )
            plan_mode = "continuous"
        else:
            plan_segments, total_cost = self._select_discrete_segments(
                valid_prices, energy_needed_kwh, required_hours, charge_minutes, completion_dt
            )
            plan_mode = "split"

        if not plan_segments:
            raise ValueError("Could not build a valid charging plan")

        start_dt = min(segment["start"] for segment in plan_segments)
        end_dt = max(segment["end"] for segment in plan_segments)

        raw_two_days = [
            {"start": start.isoformat(), "price": price} for start, price in valid_prices
        ]
        schedule = self._segments_to_schedule(plan_segments, valid_prices)
        charger_speed_pct_h = round((power / capacity) * 100, 1)

        return {
            RESULT_CHARGING_SPEED: charger_speed_pct_h,
            RESULT_CHARGE_START_TIME: self._format_datetime(start_dt),
            RESULT_CHARGE_END_TIME: self._format_datetime(end_dt),
            RESULT_CHARGE_TIME: self._format_duration(charge_minutes),
            RESULT_CHARGE_COSTS: round(total_cost, 2),
            ATTR_CHARGING_SCHEDULE: schedule,
            ATTR_RAW_TWO_DAYS: raw_two_days,
            ATTR_PLAN_MODE: plan_mode,
            ATTR_CHARGER_CONTROL_ENABLED: bool(
                self.data.inputs.get(INPUT_ENABLE_CHARGER_CONTROL, False)
            ),
            ATTR_CHARGER_ENTITY: self.config.get(CONF_CHARGER_SWITCH_ENTITY) or None,
            ATTR_CHARGER_STATUS_ENTITY: self.config.get(CONF_CHARGER_STATUS_ENTITY) or None,
            ATTR_CHARGER_BACKEND: self.charger_backend,
            ATTR_LANGUAGE: self.language,
            ATTR_COUNTRY: self.country,
            ATTR_PLATE_PROVIDER: self.plate_provider,
            ATTR_CHARGER_COMMANDABLE: self.is_charger_commandable,
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
                    try:
                        slots.append((dt_util.parse_datetime(row["hour"]), float(row["price"])))
                    except (TypeError, ValueError):
                        continue

        if slots:
            dedup: dict[str, tuple[datetime, float]] = {}
            for start, price in slots:
                if start is not None:
                    dedup[start.isoformat()] = (start, price)
            return sorted(dedup.values(), key=lambda item: item[0])

        for key, offset_days in (("today", 0), ("tomorrow", 1)):
            values = attrs.get(key) or []
            if not isinstance(values, list):
                continue
            day = self._local_now().date() + timedelta(days=offset_days)
            for hour, price in enumerate(values[:24]):
                try:
                    start = dt_util.as_local(
                        dt_util.utc_from_timestamp(
                            datetime(day.year, day.month, day.day, hour, 0).timestamp()
                        )
                    )
                    slots.append((start, float(price)))
                except (TypeError, ValueError):
                    continue

        dedup: dict[str, tuple[datetime, float]] = {}
        for start, price in slots:
            dedup[start.isoformat()] = (start, price)
        return sorted(dedup.values(), key=lambda item: item[0])

    def _select_continuous_segment(
        self,
        valid_prices: list[tuple[datetime, float]],
        energy_needed_kwh: float,
        required_hours: float,
        charge_minutes: int,
        completion_dt: datetime | None,
    ) -> tuple[list[dict[str, Any]], float]:
        hours_needed = ceil(required_hours)
        best_window: list[tuple[datetime, float]] | None = None
        best_cost = float("inf")

        for idx in range(0, len(valid_prices) - hours_needed + 1):
            window = valid_prices[idx : idx + hours_needed]
            if not self._is_consecutive(window):
                continue
            start = window[0][0]
            end = start + timedelta(minutes=charge_minutes)
            if completion_dt and end > completion_dt:
                continue
            cost = self._window_cost(window, energy_needed_kwh, required_hours)
            if cost < best_cost:
                best_cost = cost
                best_window = window

        if not best_window:
            return [], 0.0
        start = best_window[0][0]
        end = start + timedelta(minutes=charge_minutes)
        return ([{"start": start, "end": end, "value": 1.0}], best_cost)

    def _select_discrete_segments(
        self,
        valid_prices: list[tuple[datetime, float]],
        energy_needed_kwh: float,
        required_hours: float,
        charge_minutes: int,
        completion_dt: datetime | None,
    ) -> tuple[list[dict[str, Any]], float]:
        hours_needed = ceil(required_hours)
        cheapest_hours = sorted(valid_prices, key=lambda item: item[1])[:hours_needed]
        chosen = sorted(cheapest_hours, key=lambda item: item[0])
        remaining_hours = required_hours
        energy_per_hour = energy_needed_kwh / required_hours
        total_cost = 0.0
        segments: list[dict[str, Any]] = []

        for start, price in chosen:
            if completion_dt and start >= completion_dt:
                continue
            fraction = min(1.0, remaining_hours)
            end = start + timedelta(hours=fraction)
            segments.append({"start": start, "end": end, "value": 1.0})
            total_cost += price * energy_per_hour * fraction
            remaining_hours -= fraction
            if remaining_hours <= 0:
                break

        if remaining_hours > 0:
            return [], 0.0
        return segments, total_cost

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

    def _window_cost(
        self,
        window: list[tuple[datetime, float]],
        energy_needed_kwh: float,
        required_hours: float,
    ) -> float:
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

    def _is_consecutive(self, window: list[tuple[datetime, float]]) -> bool:
        if not window:
            return False
        for prev, nxt in zip(window, window[1:]):
            if nxt[0] - prev[0] != timedelta(hours=1):
                return False
        return True

    async def _async_apply_charger_plan(self, plan_segments: list[dict[str, Any]]) -> None:
        self._cancel_scheduled_actions()
        if not bool(self.data.inputs.get(INPUT_ENABLE_CHARGER_CONTROL, False)):
            self._update_charger_diagnostics()
            return
        if not self.is_charger_commandable:
            self.data.results[RESULT_CHARGER_LAST_RESULT] = "charger_not_configured"
            self._update_charger_diagnostics()
            return

        now = self._local_now()
        for segment in plan_segments:
            start = segment["start"]
            end = segment["end"]
            if end <= now:
                continue
            if start <= now < end:
                await self._async_set_charger_state(True, reason="plan_start_immediate")
                self._scheduled_callbacks.append(
                    async_track_point_in_time(
                        self.hass, self._make_charger_callback(False), end
                    )
                )
            else:
                self._scheduled_callbacks.append(
                    async_track_point_in_time(
                        self.hass, self._make_charger_callback(True), start
                    )
                )
                self._scheduled_callbacks.append(
                    async_track_point_in_time(
                        self.hass, self._make_charger_callback(False), end
                    )
                )

        await self._async_reconcile_charger_state("plan_apply")
        self._update_charger_diagnostics()

    def _cancel_scheduled_actions(self) -> None:
        while self._scheduled_callbacks:
            remove = self._scheduled_callbacks.pop()
            remove()

    def _make_charger_callback(self, turn_on: bool):
        @callback
        def _callback(_now) -> None:
            reason = "scheduled_start" if turn_on else "scheduled_stop"
            self.hass.async_create_task(self._async_set_charger_state(turn_on, reason=reason))

        return _callback

    async def _async_reconcile_charger_state(self, reason: str) -> None:
        if not bool(self.data.inputs.get(INPUT_ENABLE_CHARGER_CONTROL, False)):
            self._update_charger_diagnostics()
            return
        if not self.is_charger_commandable:
            self._update_charger_diagnostics()
            return
        expected = self.expected_charger_on
        actual = self.actual_charger_on
        if actual is None:
            if expected:
                await self._async_set_charger_state(True, reason=reason)
        elif actual != expected:
            await self._async_set_charger_state(expected, reason=reason)
        self._update_charger_diagnostics()

    async def _async_set_charger_state(self, turn_on: bool, reason: str) -> None:
        if self.uses_dummy_backend:
            await self.async_set_dummy_charger_state(turn_on, reason)
            return

        try:
            service_name = (
                self.config.get(CONF_CHARGER_START_SERVICE)
                if turn_on
                else self.config.get(CONF_CHARGER_STOP_SERVICE)
            )
            service_data_text = (
                self.config.get(CONF_CHARGER_START_DATA)
                if turn_on
                else self.config.get(CONF_CHARGER_STOP_DATA)
            )
            if service_name:
                domain, service = self._split_service(service_name)
                service_data = self._parse_service_data(service_data_text)
                charger_entity = self.config.get(CONF_CHARGER_SWITCH_ENTITY)
                if charger_entity and "entity_id" not in service_data:
                    service_data["entity_id"] = charger_entity
                await self.hass.services.async_call(
                    domain,
                    service,
                    service_data,
                    blocking=True,
                )
            else:
                charger_entity = self.config.get(CONF_CHARGER_SWITCH_ENTITY)
                if not charger_entity:
                    raise HomeAssistantError("charger_not_configured")
                domain = charger_entity.split(".", 1)[0]
                service = "turn_on" if turn_on else "turn_off"
                await self.hass.services.async_call(
                    domain,
                    service,
                    {"entity_id": charger_entity},
                    blocking=True,
                )
            self.data.results[RESULT_CHARGER_LAST_COMMAND] = (
                "turn_on" if turn_on else "turn_off"
            )
            self.data.results[RESULT_CHARGER_LAST_RESULT] = "ok"
        except (HomeAssistantError, ValueError, JSONDecodeError) as err:
            self.data.results[RESULT_CHARGER_LAST_COMMAND] = (
                "turn_on" if turn_on else "turn_off"
            )
            self.data.results[RESULT_CHARGER_LAST_RESULT] = f"error: {err}"
            _LOGGER.warning("EV Guest charger command failed: %s", err)
        finally:
            self.data.results[ATTR_LAST_CHARGER_COMMAND_AT] = self._local_now().isoformat()
            self.data.results[ATTR_LAST_CHARGER_COMMAND_REASON] = reason
            self._update_charger_diagnostics()
            self.async_update_listeners()

    def _split_service(self, value: str) -> tuple[str, str]:
        if not value or "." not in value:
            raise ValueError("service must be in domain.service format")
        domain, service = value.split(".", 1)
        if not domain or not service:
            raise ValueError("service must be in domain.service format")
        return domain, service

    def _parse_service_data(self, raw: str | None) -> dict[str, Any]:
        if not raw:
            return {}
        parsed = json_loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("service data must be a JSON object")
        return parsed

    def _read_actual_charger_state(self) -> bool | None:
        if self.uses_dummy_backend:
            return self._dummy_charger_on
        status_entity = self.config.get(CONF_CHARGER_STATUS_ENTITY) or self.config.get(
            CONF_CHARGER_SWITCH_ENTITY
        )
        if not status_entity:
            return None
        state = self.hass.states.get(status_entity)
        if state is None:
            return None
        if state.state in (STATE_ON, "charging", "connected_charging"):
            return True
        if state.state in (STATE_OFF, "idle", "paused"):
            return False
        return None

    def _update_charger_diagnostics(self) -> None:
        now = self._local_now()
        next_start = None
        next_stop = None
        active_window = None
        for segment in self._plan_segments:
            if segment["start"] <= now < segment["end"]:
                active_window = (
                    f"{self._format_datetime(segment['start'])} → "
                    f"{self._format_datetime(segment['end'])}"
                )
            if segment["start"] > now and next_start is None:
                next_start = self._format_datetime(segment["start"])
            if segment["end"] > now and next_stop is None:
                next_stop = self._format_datetime(segment["end"])

        actual_on = self.actual_charger_on
        self.data.results.update(
            {
                RESULT_CHARGER_BACKEND: self.charger_backend,
                RESULT_CHARGER_TARGET_STATE: "on" if self.expected_charger_on else "off",
                RESULT_CHARGER_ACTUAL_STATE: (
                    "on" if actual_on else "off" if actual_on is False else "unknown"
                ),
                RESULT_CHARGER_NEXT_START: next_start,
                RESULT_CHARGER_NEXT_STOP: next_stop,
                RESULT_CHARGER_ACTIVE_WINDOW: active_window,
                ATTR_CHARGER_CONTROL_ENABLED: bool(
                    self.data.inputs.get(INPUT_ENABLE_CHARGER_CONTROL, False)
                ),
                ATTR_CHARGER_ENTITY: self.config.get(CONF_CHARGER_SWITCH_ENTITY) or None,
                ATTR_CHARGER_STATUS_ENTITY: self.config.get(CONF_CHARGER_STATUS_ENTITY)
                or None,
                ATTR_CHARGER_BACKEND: self.charger_backend,
            ATTR_LANGUAGE: self.language,
            ATTR_COUNTRY: self.country,
            ATTR_PLATE_PROVIDER: self.plate_provider,
                ATTR_CHARGER_COMMANDABLE: self.is_charger_commandable,
                ATTR_CHARGER_EXPECTED_ON: self.expected_charger_on,
                ATTR_CHARGER_MISMATCH: self.charger_state_mismatch,
                ATTR_DUMMY_CHARGER: self.uses_dummy_backend,
                ATTR_CONTROL_TICK_INTERVAL: str(CONTROL_VERIFY_INTERVAL),
            }
        )

    def _local_now(self) -> datetime:
        return dt_util.now()

    def _next_completion_datetime(self, now: datetime, completion: time) -> datetime:
        dt_value = now.replace(
            hour=completion.hour,
            minute=completion.minute,
            second=0,
            microsecond=0,
        )
        if dt_value <= now:
            dt_value += timedelta(days=1)
        return dt_value

    def _format_datetime(self, value: datetime) -> str:
        if self.config.get(CONF_TIME_FORMAT) == TIME_FORMAT_12H:
            return value.strftime("%I:%M %p").lstrip("0")
        return value.strftime("%H:%M")

    def _format_duration(self, minutes: int) -> str | int:
        if self.config.get(CONF_DURATION_FORMAT) == DURATION_FORMAT_HM:
            hours, rem = divmod(minutes, 60)
            return f"{hours}h {rem}m"
        return minutes
