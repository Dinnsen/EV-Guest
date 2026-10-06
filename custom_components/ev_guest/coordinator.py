"""Coordinator for EV Guest."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
import logging
from math import ceil
from typing import Any, NoReturn

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError, HomeAssistantError, ServiceValidationError
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_point_in_time, async_track_state_change_event
from homeassistant.helpers.start import async_at_started
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
    ATTR_FUEL_TYPE,
    ATTR_LAST_CALCULATION,
    ATTR_LAST_LOOKUP,
    ATTR_LAST_SOURCE,
    ATTR_MATCH_SCORE,
    ATTR_MODEL_YEAR,
    ATTR_PLAN_MODE,
    ATTR_RAW_TWO_DAYS,
    ATTR_VIN,
    CONF_COUNTRY,
    CONF_CURRENCY,
    CONF_MOTORAPI_KEY,
    CONF_PLATE_PROVIDER,
    CONF_PRICE_ENTITY,
    DEFAULT_COMPLETION_TIME,
    DEFAULT_COUNTRY,
    DEFAULT_CURRENCY,
    DOMAIN,
    ERROR_INVALID_API_KEY,
    ERROR_INVALID_INPUT,
    ERROR_LICENSE_PLATE_REQUIRED,
    ERROR_LIMIT_NOT_ABOVE_SOC,
    ERROR_LOOKUP_FAILED,
    ERROR_MOTORAPI_KEY_MISSING,
    ERROR_NO_PRICE_DATA,
    ERROR_NO_WINDOW,
    ERROR_NOT_ENOUGH_PRICES,
    ERROR_VEHICLE_NOT_FOUND,
    INPUT_BATTERY_CAPACITY,
    INPUT_CHARGE_COMPLETION_TIME,
    INPUT_CHARGE_LIMIT,
    INPUT_CHARGER_POWER,
    INPUT_CONTINUOUS_CHARGING_PREFERRED,
    INPUT_LICENSE_PLATE,
    INPUT_SOC,
    INPUT_USE_COMPLETION_TIME,
    ISSUE_PRICE_ENTITY_MISSING,
    RESULT_CAR_BATTERY_CAPACITY,
    RESULT_CAR_BRAND,
    RESULT_CAR_MODEL,
    RESULT_CAR_VARIANT,
    RESULT_CHARGE_COSTS,
    RESULT_CHARGE_TIME,
    RESULT_CHARGING_SPEED,
    STATUS_CHARGING,
    STATUS_COMPLETED,
    STATUS_PLANNED,
    STATUS_READY,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .prices import PriceSlot, extract_price_slots

_LOGGER = logging.getLogger(__name__)

type EVGuestConfigEntry = ConfigEntry[EVGuestCoordinator]
type Segment = dict[str, datetime]


class PlanError(Exception):
    """A charging plan could not be made; ``key`` is a status/translation key."""

    def __init__(self, key: str) -> None:
        super().__init__(key)
        self.key = key


@dataclass(slots=True)
class EVGuestData:
    """Coordinator state."""

    inputs: dict[str, Any]
    results: dict[str, Any]
    service_health: dict[str, bool]


class EVGuestCoordinator(DataUpdateCoordinator[EVGuestData]):
    """Central state holder and calculator.

    EV Guest does not poll anything: it reacts to price sensor updates, user
    input and the start/end of planned charging segments.
    """

    config_entry: EVGuestConfigEntry

    def __init__(self, hass: HomeAssistant, entry: EVGuestConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=None,
        )
        self.session = async_get_clientsession(hass)
        self._unsub: list[CALLBACK_TYPE] = []
        self._availability_logged: dict[str, bool] = {}
        self._boundary_callbacks: list[CALLBACK_TYPE] = []
        # Planned charging intervals. This is the source of truth for
        # charge_now and the plan sensors; charging_schedule is per hour and
        # only meant for graphs.
        self._plan_segments: list[Segment] = []
        # Automatic recalculation on price updates is only allowed after the
        # user has requested a calculation, and only until the plan starts.
        self._auto_recalculate = False
        self._error: str | None = None
        self._error_detail: str | None = None
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY.format(entry_id=entry.entry_id))
        self.data = EVGuestData(
            inputs={
                INPUT_LICENSE_PLATE: "",
                INPUT_SOC: 20.0,
                INPUT_BATTERY_CAPACITY: 77.0,
                INPUT_CHARGER_POWER: 11.0,
                INPUT_CHARGE_LIMIT: 80.0,
                INPUT_CHARGE_COMPLETION_TIME: DEFAULT_COMPLETION_TIME,
                INPUT_USE_COMPLETION_TIME: True,
                INPUT_CONTINUOUS_CHARGING_PREFERRED: True,
            },
            results={
                RESULT_CHARGING_SPEED: None,
                RESULT_CHARGE_TIME: None,
                RESULT_CHARGE_COSTS: None,
                RESULT_CAR_BRAND: None,
                RESULT_CAR_MODEL: None,
                RESULT_CAR_VARIANT: None,
                RESULT_CAR_BATTERY_CAPACITY: None,
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
            },
            service_health={"motorapi": True, "nhtsa": True, "open_ev_data": True},
        )

    # ------------------------------------------------------------------
    # Configuration

    @property
    def config(self) -> dict[str, Any]:
        return {**self.config_entry.data, **self.config_entry.options}

    @property
    def price_entity(self) -> str:
        return self.config[CONF_PRICE_ENTITY]

    @property
    def currency(self) -> str:
        return self.config.get(CONF_CURRENCY) or self.hass.config.currency or DEFAULT_CURRENCY

    @property
    def country(self) -> str:
        return self.config.get(CONF_COUNTRY, DEFAULT_COUNTRY)

    @property
    def plate_provider(self) -> str:
        return self.config.get(CONF_PLATE_PROVIDER) or get_default_plate_provider(self.country)

    @property
    def has_motorapi_key(self) -> bool:
        return bool(str(self.config.get(CONF_MOTORAPI_KEY) or "").strip())

    # ------------------------------------------------------------------
    # Lifecycle

    async def async_initialize(self) -> None:
        await self._async_validate_setup()
        await self._async_load_state()
        self._unsub.append(async_track_state_change_event(self.hass, [self.price_entity], self._handle_price_update))
        self._unsub.append(async_at_started(self.hass, self._async_check_price_entity))
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
            raise ConfigEntryAuthFailed(translation_domain=DOMAIN, translation_key="invalid_api_key") from err
        except EVGuestLookupError as err:
            if str(err) == "unsupported_provider":
                raise ConfigEntryError(translation_domain=DOMAIN, translation_key="unsupported_provider") from err
            _LOGGER.warning("Could not validate MotorAPI key during setup: %s", err)
            self._set_service_health("motorapi", False)

    async def async_shutdown(self) -> None:
        while self._unsub:
            self._unsub.pop()()
        self._cancel_plan_boundaries()
        await super().async_shutdown()

    async def _async_update_data(self) -> EVGuestData:
        return self.data

    @callback
    def _async_check_price_entity(self, _hass: HomeAssistant | None = None) -> None:
        """Raise or clear a repair issue for a missing price sensor."""
        issue_id = f"{ISSUE_PRICE_ENTITY_MISSING}_{self.config_entry.entry_id}"
        if self.hass.states.get(self.price_entity) is None:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                issue_id,
                is_fixable=False,
                severity=ir.IssueSeverity.ERROR,
                translation_key=ISSUE_PRICE_ENTITY_MISSING,
                translation_placeholders={
                    "entity_id": self.price_entity,
                    "title": self.config_entry.title,
                },
            )
        else:
            ir.async_delete_issue(self.hass, DOMAIN, issue_id)

    @callback
    def _handle_price_update(self, event: Event[EventStateChangedData]) -> None:
        if event.data["new_state"] is not None:
            self._async_check_price_entity()
        if not self._auto_recalculate or self.is_plan_locked():
            return
        self.config_entry.async_create_background_task(
            self.hass, self.async_calculate(manual=False), f"{DOMAIN} recalculate"
        )

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
        # 0.7.x stored the completion time as text (possibly 12h) and the
        # charge time as text when "hours_minutes" was selected.
        completion = parse_time(self.data.inputs.get(INPUT_CHARGE_COMPLETION_TIME))
        self.data.inputs[INPUT_CHARGE_COMPLETION_TIME] = format_time(completion or parse_time(DEFAULT_COMPLETION_TIME))
        if not isinstance(self.data.results.get(RESULT_CHARGE_TIME), int | float):
            self.data.results[RESULT_CHARGE_TIME] = None
        self._plan_segments = parse_segments(stored.get("segments") or [])
        self._auto_recalculate = bool(stored.get("auto_recalculate", False))

    @callback
    def _async_save_state(self) -> None:
        self._store.async_delay_save(self._data_to_store, 1)

    @callback
    def _data_to_store(self) -> dict[str, Any]:
        return {
            "inputs": dict(self.data.inputs),
            "results": dict(self.data.results),
            "segments": serialize_segments(self._plan_segments),
            "auto_recalculate": self._auto_recalculate,
        }

    # ------------------------------------------------------------------
    # Inputs

    async def async_set_input_value(self, key: str, value: Any) -> None:
        if key == INPUT_CHARGE_COMPLETION_TIME:
            value = format_time(value) if isinstance(value, time) else format_time(parse_time(value))
        self.data.inputs[key] = value
        self._async_save_state()
        self.async_update_listeners()

    @property
    def completion_time(self) -> time:
        return parse_time(self.data.inputs.get(INPUT_CHARGE_COMPLETION_TIME)) or parse_time(DEFAULT_COMPLETION_TIME)

    # ------------------------------------------------------------------
    # Status

    @property
    def error_detail(self) -> str | None:
        return self._error_detail

    @callback
    def _set_error(self, key: str | None, detail: str | None = None) -> None:
        self._error = key
        self._error_detail = detail

    def status(self, now: datetime | None = None) -> str:
        if self._error:
            return self._error
        if not self._plan_segments:
            return STATUS_READY
        now = now or dt_util.now()
        if self.is_charge_now(now):
            return STATUS_CHARGING
        if now >= self._plan_segments[-1]["end"]:
            return STATUS_COMPLETED
        return STATUS_PLANNED

    @property
    def plan_start(self) -> datetime | None:
        return self._plan_segments[0]["start"] if self._plan_segments else None

    @property
    def plan_end(self) -> datetime | None:
        return self._plan_segments[-1]["end"] if self._plan_segments else None

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

    # ------------------------------------------------------------------
    # Vehicle lookup

    async def async_lookup_car_data(self) -> None:
        """Look up the guest car from its license plate.

        Raises a translated error so the button press or action call shows
        why it failed; the status sensor shows the same reason.
        """
        plate = str(self.data.inputs.get(INPUT_LICENSE_PLATE) or "").strip()
        if not plate:
            self._fail(ERROR_LICENSE_PLATE_REQUIRED)
        if not self.has_motorapi_key:
            self._fail(ERROR_MOTORAPI_KEY_MISSING)

        try:
            motor = await async_lookup_vehicle(
                self.session,
                plate,
                self.config[CONF_MOTORAPI_KEY],
                self.country,
                self.plate_provider,
            )
            self._set_service_health("motorapi", True)
        except EVGuestAuthError as err:
            self._set_service_health("motorapi", False)
            self.config_entry.async_start_reauth(self.hass)
            self._fail(ERROR_INVALID_API_KEY, cause=err)
        except EVGuestLookupError as err:
            reason = str(err)
            self._set_service_health("motorapi", reason not in {"cannot_connect", "timeout"})
            if reason == "vehicle_not_found":
                self._fail(ERROR_VEHICLE_NOT_FOUND, cause=err)
            self._fail(ERROR_LOOKUP_FAILED, detail=reason, cause=err, service_error=True)

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
                ATTR_LAST_LOOKUP: dt_util.now().isoformat(),
            }
        )
        if battery.battery_capacity:
            self.data.inputs[INPUT_BATTERY_CAPACITY] = battery.battery_capacity
        self._async_save_state()
        self.async_update_listeners()

    def _fail(
        self,
        key: str,
        *,
        detail: str | None = None,
        cause: Exception | None = None,
        service_error: bool = False,
        show_in_status: bool = False,
    ) -> NoReturn:
        """Raise ``key`` as a translated error.

        Calculation errors are also shown on the status sensor. Lookup errors
        are not, so a failed lookup never hides the state of an active plan.
        """
        if show_in_status:
            self._set_error(key, detail)
            self.async_update_listeners()
        error_cls = HomeAssistantError if service_error else ServiceValidationError
        raise error_cls(
            translation_domain=DOMAIN,
            translation_key=key,
            translation_placeholders={"detail": detail} if detail else None,
        ) from cause

    @staticmethod
    def _merge_vehicle_results(
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

    # ------------------------------------------------------------------
    # Planning

    async def async_calculate(self, manual: bool = True) -> None:
        """Calculate the cheapest charging plan.

        EV Guest only knows the SoC at the time of calculation, it never sees
        the car's live SoC. A plan is therefore locked once it has started:
        automatic recalculations (price updates) are skipped from then on, so
        a static start SoC can never make the plan slide or repeat. A manual
        calculation always makes a fresh plan and raises a translated error
        when no plan can be made.
        """
        if manual:
            self._auto_recalculate = True
        elif self.is_plan_locked():
            return

        try:
            calculation = self._calculate_schedule()
        except PlanError as err:
            if manual:
                # Do not keep following an old plan the user tried to replace.
                self._set_plan([])
                self._async_save_state()
                self._fail(err.key, cause=err, show_in_status=True)
            if not self._plan_segments:
                self._set_error(err.key)
                self.async_update_listeners()
            return

        segments = calculation.pop("plan_segments")
        self.data.results.update(calculation)
        self.data.results[ATTR_LAST_CALCULATION] = dt_util.now().isoformat()
        self._set_error(None)
        self._set_plan(segments)
        self._async_save_state()
        self.async_update_listeners()

    def _calculate_schedule(self) -> dict[str, Any]:
        try:
            soc = float(self.data.inputs[INPUT_SOC])
            battery_capacity = float(self.data.inputs[INPUT_BATTERY_CAPACITY])
            charger_power = float(self.data.inputs[INPUT_CHARGER_POWER])
            charge_limit = float(self.data.inputs[INPUT_CHARGE_LIMIT])
        except (TypeError, ValueError) as err:
            raise PlanError(ERROR_INVALID_INPUT) from err
        use_completion_time = bool(self.data.inputs.get(INPUT_USE_COMPLETION_TIME, True))
        continuous = bool(self.data.inputs.get(INPUT_CONTINUOUS_CHARGING_PREFERRED, True))

        if battery_capacity <= 0 or charger_power <= 0 or not 0 <= soc <= 100 or not 0 <= charge_limit <= 100:
            raise PlanError(ERROR_INVALID_INPUT)
        if charge_limit <= soc:
            raise PlanError(ERROR_LIMIT_NOT_ABOVE_SOC)

        speed_pct_per_hour = (charger_power / battery_capacity) * 100
        energy_needed_kwh = battery_capacity * ((charge_limit - soc) / 100)
        charge_minutes = ceil((energy_needed_kwh / charger_power) * 60)
        required_hours = charge_minutes / 60
        hours_needed = ceil(required_hours)

        now = dt_util.now()
        prices = extract_price_slots(self.hass.states.get(self.price_entity), now)
        if not prices:
            raise PlanError(ERROR_NO_PRICE_DATA)

        visible_prices = prices[:48]
        self.data.results[ATTR_RAW_TWO_DAYS] = [
            {"start": start.isoformat(), "value": price} for start, price in visible_prices
        ]

        planning_prices = prices if use_completion_time else visible_prices
        valid_prices = [slot for slot in planning_prices if now <= slot[0]]
        completion_dt = None
        if use_completion_time:
            completion_dt = next_completion_datetime(now, self.completion_time)
            valid_prices = [slot for slot in valid_prices if slot[0] < completion_dt]
        if len(valid_prices) < hours_needed:
            raise PlanError(ERROR_NOT_ENOUGH_PRICES)

        if continuous:
            plan_segments, plan_cost = select_continuous_segments(
                valid_prices, energy_needed_kwh, required_hours, charge_minutes, completion_dt
            )
            mode = "continuous"
        else:
            plan_segments, plan_cost = select_split_segments(
                valid_prices, energy_needed_kwh, required_hours, completion_dt
            )
            mode = "split"

        if not plan_segments:
            raise PlanError(ERROR_NO_WINDOW)

        self.data.results[ATTR_CHARGING_SCHEDULE] = segments_to_schedule(plan_segments, visible_prices)
        self.data.results[ATTR_PLAN_MODE] = mode

        return {
            RESULT_CHARGING_SPEED: round(speed_pct_per_hour, 1),
            RESULT_CHARGE_TIME: charge_minutes,
            RESULT_CHARGE_COSTS: round(plan_cost, 2),
            "plan_segments": plan_segments,
        }

    # ------------------------------------------------------------------
    # Plan state and charge_now

    @callback
    def _set_plan(self, segments: list[Segment]) -> None:
        self._plan_segments = [{"start": seg["start"], "end": seg["end"]} for seg in segments]
        self.data.results[ATTR_CHARGING_SEGMENTS] = serialize_segments(self._plan_segments)
        if not segments:
            self.data.results[ATTR_CHARGING_SCHEDULE] = []
        self._schedule_plan_boundaries()

    @callback
    def _schedule_plan_boundaries(self) -> None:
        """Push a state update exactly when charge_now should change."""
        self._cancel_plan_boundaries()
        now = dt_util.now()
        for segment in self._plan_segments:
            for moment in (segment["start"], segment["end"]):
                if moment > now:
                    self._boundary_callbacks.append(
                        async_track_point_in_time(self.hass, self._handle_plan_boundary, moment)
                    )

    @callback
    def _cancel_plan_boundaries(self) -> None:
        while self._boundary_callbacks:
            self._boundary_callbacks.pop()()

    @callback
    def _handle_plan_boundary(self, _now: datetime) -> None:
        self.async_update_listeners()

    def is_plan_locked(self, now: datetime | None = None) -> bool:
        """True once the current plan has started (also after it has finished)."""
        if not self._plan_segments:
            return False
        now = now or dt_util.now()
        return self._plan_segments[0]["start"] <= now

    def is_charge_now(self, now: datetime | None = None) -> bool:
        now = now or dt_util.now()
        return any(segment["start"] <= now < segment["end"] for segment in self._plan_segments)


# ----------------------------------------------------------------------
# Pure helpers (unit tested directly)


def parse_time(value: Any) -> time | None:
    if isinstance(value, time):
        return value
    if value is None:
        return None
    text = str(value).strip()
    for fmt in ("%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M%p"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    return None


def format_time(value: time | None) -> str:
    return (value or parse_time(DEFAULT_COMPLETION_TIME)).strftime("%H:%M")  # type: ignore[union-attr]


def next_completion_datetime(now: datetime, completion: time) -> datetime:
    result = now.replace(hour=completion.hour, minute=completion.minute, second=0, microsecond=0)
    if result <= now:
        result += timedelta(days=1)
    return result


def serialize_segments(segments: list[Segment]) -> list[dict[str, str]]:
    return [{"start": seg["start"].isoformat(), "end": seg["end"].isoformat()} for seg in segments]


def parse_segments(raw: list[Any]) -> list[Segment]:
    segments: list[Segment] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        start = dt_util.parse_datetime(str(item.get("start", "")))
        end = dt_util.parse_datetime(str(item.get("end", "")))
        if start is None or end is None or end <= start:
            continue
        segments.append({"start": start, "end": end})
    return sorted(segments, key=lambda seg: seg["start"])


def _window_cost(window: list[PriceSlot], energy_needed_kwh: float, required_hours: float) -> float:
    """Cost of charging from the start of ``window``; the last hour may be partial."""
    energy_per_hour = energy_needed_kwh / required_hours
    full_hours = int(required_hours)
    cost = sum(price for _start, price in window[:full_hours]) * energy_per_hour
    if len(window) > full_hours:
        cost += window[full_hours][1] * energy_per_hour * (required_hours - full_hours)
    return cost


def select_continuous_segments(
    valid_prices: list[PriceSlot],
    energy_needed_kwh: float,
    required_hours: float,
    charge_minutes: int,
    completion_dt: datetime | None,
) -> tuple[list[Segment], float]:
    """Cheapest single block of consecutive hours."""
    hours_needed = ceil(required_hours)
    best: tuple[list[PriceSlot], float] | None = None
    for index in range(len(valid_prices) - hours_needed + 1):
        window = valid_prices[index : index + hours_needed]
        if completion_dt and window[-1][0] + timedelta(hours=1) > completion_dt:
            continue
        cost = _window_cost(window, energy_needed_kwh, required_hours)
        if best is None or cost < best[1]:
            best = (window, cost)

    if best is None:
        return [], 0.0
    start = best[0][0][0]
    return [{"start": start, "end": start + timedelta(minutes=charge_minutes)}], best[1]


def select_split_segments(
    valid_prices: list[PriceSlot],
    energy_needed_kwh: float,
    required_hours: float,
    completion_dt: datetime | None,
) -> tuple[list[Segment], float]:
    """Cheapest hours, not necessarily adjacent.

    Full hours go to the cheapest slots. A remaining partial hour goes to the
    next-cheapest slot (the most expensive one chosen), which is the cheapest
    possible split. Slots must end before the completion time.
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
    segments: list[Segment] = []
    for start, price in full_slots:
        segments.append({"start": start, "end": start + timedelta(hours=1)})
        total_cost += price * energy_per_hour

    if fraction > 1e-9:
        start, price = by_price[full_hours]
        duration = timedelta(hours=fraction)
        slot_end = start + timedelta(hours=1)
        if slot_end in full_starts:
            # Place the partial charge at the end of its hour so it joins the
            # following charging hour instead of leaving a gap.
            segments.append({"start": slot_end - duration, "end": slot_end})
        else:
            segments.append({"start": start, "end": start + duration})
        total_cost += price * energy_per_hour * fraction

    return merge_segments(segments), total_cost


def merge_segments(segments: list[Segment]) -> list[Segment]:
    merged: list[Segment] = []
    for segment in sorted(segments, key=lambda seg: seg["start"]):
        if merged and segment["start"] <= merged[-1]["end"]:
            merged[-1]["end"] = max(merged[-1]["end"], segment["end"])
        else:
            merged.append({"start": segment["start"], "end": segment["end"]})
    return merged


def segments_to_schedule(segments: list[Segment], price_slots: list[PriceSlot]) -> list[dict[str, Any]]:
    """Per-hour 0/1 view of the plan, aligned with raw_two_days, for graphs."""
    output: list[dict[str, Any]] = []
    for start, _price in price_slots:
        end = start + timedelta(hours=1)
        active = any(seg["start"] < end and seg["end"] > start for seg in segments)
        output.append({"start": start.isoformat(), "value": 1.0 if active else 0.0})
    return output
