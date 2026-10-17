"""Coordinator for EV Guest."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, time, timedelta
import logging
from typing import Any, NoReturn
from uuid import uuid4

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN, UnitOfEnergy
from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, HomeAssistant, State, callback
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError, HomeAssistantError, ServiceValidationError
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import (
    async_track_point_in_time,
    async_track_state_change_event,
    async_track_time_interval,
)
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
    ATTR_AVERAGE_PRICE,
    ATTR_CHARGE_NOW_COST,
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
    CONF_ENERGY_ENTITY,
    CONF_MOTORAPI_KEY,
    CONF_PLATE_PROVIDER,
    CONF_PRICE_ENTITY,
    DATASET_CACHE_KEY,
    DEFAULT_CHARGING_EFFICIENCY,
    DEFAULT_COMPLETION_TIME,
    DEFAULT_COUNTRY,
    DEFAULT_CURRENCY,
    DOMAIN,
    ERROR_INVALID_API_KEY,
    ERROR_INVALID_INPUT,
    ERROR_LICENSE_PLATE_REQUIRED,
    ERROR_LOOKUP_FAILED,
    ERROR_MOTORAPI_KEY_MISSING,
    ERROR_VEHICLE_NOT_FOUND,
    HISTORY_LIMIT,
    INPUT_BATTERY_CAPACITY,
    INPUT_CHARGE_COMPLETION_TIME,
    INPUT_CHARGE_LIMIT,
    INPUT_CHARGER_POWER,
    INPUT_CHARGING_EFFICIENCY,
    INPUT_CONTINUOUS_CHARGING_PREFERRED,
    INPUT_LICENSE_PLATE,
    INPUT_SOC,
    INPUT_USE_COMPLETION_TIME,
    ISSUE_PRICE_ENTITY_MISSING,
    METER_GRACE,
    PLANNING_HORIZON,
    PROGRESS_INTERVAL,
    RESULT_CAR_BATTERY_CAPACITY,
    RESULT_CAR_BRAND,
    RESULT_CAR_MODEL,
    RESULT_CAR_VARIANT,
    RESULT_CHARGE_COSTS,
    RESULT_CHARGE_TIME,
    RESULT_CHARGING_SPEED,
    RESULT_ENERGY,
    RESULT_MEASURED_COST,
    RESULT_MEASURED_ENERGY,
    RESULT_SAVINGS,
    STATUS_CHARGING,
    STATUS_COMPLETED,
    STATUS_PLANNED,
    STATUS_READY,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .planner import (
    Plan,
    PlanError,
    PriceSlot,
    Segment,
    charge_need,
    make_plan,
    merge_segments,
    price_at,
    segments_to_schedule,
)
from .prices import extract_price_slots
from .progress import Progress, plan_progress

_LOGGER = logging.getLogger(__name__)

type EVGuestConfigEntry = ConfigEntry[EVGuestCoordinator]

__all__ = ["EVGuestConfigEntry", "EVGuestCoordinator", "PlanError", "merge_segments"]

CAR_RESULTS = (
    RESULT_CAR_BRAND,
    RESULT_CAR_MODEL,
    RESULT_CAR_VARIANT,
    RESULT_CAR_BATTERY_CAPACITY,
    ATTR_VIN,
    ATTR_MODEL_YEAR,
    ATTR_FUEL_TYPE,
    ATTR_MATCH_SCORE,
    ATTR_LAST_SOURCE,
    ATTR_LAST_LOOKUP,
)
PLAN_RESULTS = (
    RESULT_CHARGING_SPEED,
    RESULT_CHARGE_TIME,
    RESULT_CHARGE_COSTS,
    RESULT_ENERGY,
    RESULT_SAVINGS,
    ATTR_CHARGE_NOW_COST,
    ATTR_AVERAGE_PRICE,
)
SETTING_BILL_PRICE = "bill_price"
SETTING_PAYMENT_TEXT = "payment_text"
DEFAULT_SETTINGS: dict[str, Any] = {SETTING_BILL_PRICE: None, SETTING_PAYMENT_TEXT: ""}
# A single meter step above this is a glitch, not a charge.
MAX_METER_STEP_KWH = 100.0


@dataclass(slots=True)
class EVGuestData:
    """Coordinator state."""

    inputs: dict[str, Any]
    results: dict[str, Any]
    service_health: dict[str, bool]


class EVGuestCoordinator(DataUpdateCoordinator[EVGuestData]):
    """Central state holder and calculator.

    EV Guest does not poll anything: it reacts to price sensor updates, the
    optional energy meter, user input and the start/end of planned charging
    segments.
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
        # Updates the estimated charge level while a charging period runs.
        self._progress_tick: CALLBACK_TYPE | None = None
        # Planned charging intervals. This is the source of truth for
        # charge_now and the plan sensors; charging_schedule is per price
        # slot and only meant for graphs.
        self._plan_segments: list[Segment] = []
        # Automatic recalculation on price updates is only allowed after the
        # user has requested a calculation, and only until the plan starts.
        self._auto_recalculate = False
        self._error: str | None = None
        self._error_detail: str | None = None
        # The guest and figures the current plan was made for, for history.
        self._plan_info: dict[str, Any] | None = None
        self._recorded = False
        self._meter_last: float | None = None
        self.history: list[dict[str, Any]] = []
        self.settings: dict[str, Any] = dict(DEFAULT_SETTINGS)
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
                INPUT_CHARGING_EFFICIENCY: DEFAULT_CHARGING_EFFICIENCY,
            },
            results={
                **dict.fromkeys(PLAN_RESULTS),
                **dict.fromkeys(CAR_RESULTS),
                ATTR_LAST_CALCULATION: None,
                ATTR_CHARGING_SCHEDULE: [],
                ATTR_RAW_TWO_DAYS: [],
                ATTR_PLAN_MODE: "continuous",
                ATTR_CHARGING_SEGMENTS: [],
                RESULT_MEASURED_ENERGY: None,
                RESULT_MEASURED_COST: None,
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
        return str(self.config[CONF_PRICE_ENTITY])

    @property
    def energy_entity(self) -> str | None:
        return self.config.get(CONF_ENERGY_ENTITY) or None

    @property
    def currency(self) -> str:
        return str(self.config.get(CONF_CURRENCY) or self.hass.config.currency or DEFAULT_CURRENCY)

    @property
    def country(self) -> str:
        return str(self.config.get(CONF_COUNTRY, DEFAULT_COUNTRY))

    @property
    def plate_provider(self) -> str:
        return str(self.config.get(CONF_PLATE_PROVIDER) or get_default_plate_provider(self.country))

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
        if self.energy_entity:
            if self._meter_last is None:
                self._meter_last = meter_kwh(self.hass.states.get(self.energy_entity))
            self._unsub.append(
                async_track_state_change_event(self.hass, [self.energy_entity], self._handle_meter_update)
            )
        self._maybe_record()
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
        self._stop_progress_tick()
        # Write now instead of after the save delay: a reload (e.g. after an
        # options change) would otherwise load the state from before.
        await self._store.async_save(self._data_to_store())
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
            # The panel shows prices, so it still wants to hear about them.
            self.async_update_listeners()
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
        info = stored.get("plan_info")
        self._plan_info = info if isinstance(info, dict) else None
        # Plans from before 0.9.0 have no info and are never added to history.
        self._recorded = bool(stored.get("recorded", self._plan_info is None))
        meter = stored.get("meter_last")
        self._meter_last = float(meter) if isinstance(meter, int | float) else None
        self.history = [entry for entry in stored.get("history") or [] if isinstance(entry, dict)][:HISTORY_LIMIT]
        self.settings = {**DEFAULT_SETTINGS, **(stored.get("settings") or {})}

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
            "plan_info": self._plan_info,
            "recorded": self._recorded,
            "meter_last": self._meter_last,
            "history": self.history,
            "settings": self.settings,
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
        return parse_time(self.data.inputs.get(INPUT_CHARGE_COMPLETION_TIME)) or time(7)

    # ------------------------------------------------------------------
    # Status

    @property
    def error(self) -> str | None:
        return self._error

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
    def plan_segments(self) -> list[Segment]:
        return list(self._plan_segments)

    @property
    def plan_start(self) -> datetime | None:
        return self._plan_segments[0]["start"] if self._plan_segments else None

    @property
    def plan_end(self) -> datetime | None:
        return self._plan_segments[-1]["end"] if self._plan_segments else None

    @property
    def plan_info(self) -> dict[str, Any] | None:
        return self._plan_info

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
            cache=self.hass.data.setdefault(DATASET_CACHE_KEY, {}),
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
        # Also publishes changed service health (car sensor availability).
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

    def price_slots(self, now: datetime | None = None) -> list[PriceSlot]:
        """The prices the price sensor has now."""
        return extract_price_slots(self.hass.states.get(self.price_entity), now or dt_util.now())

    def visible_slots(self, slots: list[PriceSlot]) -> list[PriceSlot]:
        """Today's and tomorrow's prices, for graphs."""
        if not slots:
            return []
        end = slots[0].start + PLANNING_HORIZON
        return [slot for slot in slots if slot.start < end]

    def make_plan(self, inputs: Mapping[str, Any], now: datetime | None = None) -> tuple[Plan, list[PriceSlot]]:
        """Plan with the given inputs; raises PlanError. Nothing is stored."""
        try:
            soc = float(inputs[INPUT_SOC])
            battery_capacity = float(inputs[INPUT_BATTERY_CAPACITY])
            charger_power = float(inputs[INPUT_CHARGER_POWER])
            charge_limit = float(inputs[INPUT_CHARGE_LIMIT])
            efficiency = float(inputs.get(INPUT_CHARGING_EFFICIENCY) or DEFAULT_CHARGING_EFFICIENCY) / 100
        except (KeyError, TypeError, ValueError) as err:
            raise PlanError(ERROR_INVALID_INPUT) from err
        need = charge_need(soc, charge_limit, battery_capacity, charger_power, efficiency)

        now = now or dt_util.now()
        slots = self.price_slots(now)
        completion = None
        if bool(inputs.get(INPUT_USE_COMPLETION_TIME, True)):
            completion_time = parse_time(inputs.get(INPUT_CHARGE_COMPLETION_TIME)) or time(7)
            completion = next_completion_datetime(now, completion_time)
        continuous = bool(inputs.get(INPUT_CONTINUOUS_CHARGING_PREFERRED, True))
        plan = make_plan(slots, need, charger_power, now, completion, PLANNING_HORIZON, continuous)
        return plan, slots

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

        now = dt_util.now()
        try:
            plan, slots = self.make_plan(self.data.inputs, now)
        except PlanError as err:
            if manual:
                # Do not keep following an old plan the user tried to replace.
                self._maybe_record(now, ended=True)
                self._clear_plan()
                self._async_save_state()
                self._fail(err.key, cause=err, show_in_status=True)
            if not self._plan_segments:
                self._set_error(err.key)
                self.async_update_listeners()
            return

        if manual or not self._plan_segments:
            # A new plan (not an update of one waiting to start) is a new session.
            self._maybe_record(now, ended=True)
            self._start_session()
        visible = self.visible_slots(slots)
        self.data.results.update(
            {
                RESULT_CHARGING_SPEED: round(plan.need.speed_pct_per_hour, 1),
                RESULT_CHARGE_TIME: plan.need.minutes,
                RESULT_CHARGE_COSTS: round(plan.cost, 2),
                RESULT_ENERGY: round(plan.need.grid_kwh, 2),
                RESULT_SAVINGS: None if plan.savings is None else round(plan.savings, 2),
                ATTR_CHARGE_NOW_COST: None if plan.charge_now_cost is None else round(plan.charge_now_cost, 2),
                ATTR_AVERAGE_PRICE: None if plan.average_price is None else round(plan.average_price, 4),
                ATTR_RAW_TWO_DAYS: [{"start": slot.start.isoformat(), "value": slot.price} for slot in visible],
                ATTR_CHARGING_SCHEDULE: segments_to_schedule(plan.segments, visible),
                ATTR_PLAN_MODE: plan.mode,
                ATTR_LAST_CALCULATION: now.isoformat(),
            }
        )
        self._plan_info = self._describe_plan(plan)
        self._set_error(None)
        self._set_plan(plan.segments)
        self._async_save_state()
        self.async_update_listeners()

    def _describe_plan(self, plan: Plan) -> dict[str, Any]:
        """What history needs to know about the guest and the plan."""
        results = self.data.results
        car = " ".join(str(part) for part in (results.get(RESULT_CAR_BRAND), results.get(RESULT_CAR_MODEL)) if part)
        return {
            "plate": str(self.data.inputs.get(INPUT_LICENSE_PLATE) or ""),
            "car": car or None,
            "variant": results.get(RESULT_CAR_VARIANT),
            "soc": self.data.inputs.get(INPUT_SOC),
            "limit": self.data.inputs.get(INPUT_CHARGE_LIMIT),
            "energy": round(plan.need.grid_kwh, 2),
            "battery_energy": round(plan.need.battery_kwh, 2),
            "cost": round(plan.cost, 2),
            "savings": None if plan.savings is None else round(plan.savings, 2),
            "mode": plan.mode,
            "currency": self.currency,
            # The inputs the plan was made with, so the panel can tell when they changed.
            "inputs": {
                key: self.data.inputs.get(key)
                for key in (
                    INPUT_SOC,
                    INPUT_CHARGE_LIMIT,
                    INPUT_BATTERY_CAPACITY,
                    INPUT_CHARGER_POWER,
                    INPUT_CHARGING_EFFICIENCY,
                    INPUT_CHARGE_COMPLETION_TIME,
                    INPUT_USE_COMPLETION_TIME,
                    INPUT_CONTINUOUS_CHARGING_PREFERRED,
                )
            },
        }

    @callback
    def _start_session(self) -> None:
        """A new plan starts a new guest session."""
        self._recorded = False
        if self.energy_entity:
            self.data.results[RESULT_MEASURED_ENERGY] = 0.0
            self.data.results[RESULT_MEASURED_COST] = 0.0
            self._meter_last = meter_kwh(self.hass.states.get(self.energy_entity))
        else:
            self.data.results[RESULT_MEASURED_ENERGY] = None
            self.data.results[RESULT_MEASURED_COST] = None

    @callback
    def _clear_plan(self) -> None:
        self._set_plan([])
        for key in PLAN_RESULTS:
            self.data.results[key] = None
        self._plan_info = None
        self._recorded = True

    async def async_new_guest(self) -> None:
        """Forget the current guest and plan, ready for the next car.

        A plan that has finished is added to the history first.
        """
        self._maybe_record(dt_util.now(), ended=True)
        self._clear_plan()
        self._set_error(None)
        self._auto_recalculate = False
        self.data.inputs[INPUT_LICENSE_PLATE] = ""
        for key in CAR_RESULTS:
            self.data.results[key] = None
        self.data.results[RESULT_MEASURED_ENERGY] = None
        self.data.results[RESULT_MEASURED_COST] = None
        self._async_save_state()
        self.async_update_listeners()

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
        moments = [moment for segment in self._plan_segments for moment in (segment["start"], segment["end"])]
        if self._plan_segments and not self._recorded:
            moments.append(self._plan_segments[-1]["end"] + METER_GRACE)
        for moment in moments:
            if moment > now:
                self._boundary_callbacks.append(
                    async_track_point_in_time(self.hass, self._handle_plan_boundary, moment)
                )
        self._update_progress_tick(now)

    @callback
    def _cancel_plan_boundaries(self) -> None:
        while self._boundary_callbacks:
            self._boundary_callbacks.pop()()

    @callback
    def _handle_plan_boundary(self, now: datetime) -> None:
        self._maybe_record(now)
        self._update_progress_tick(now)
        self.async_update_listeners()

    @callback
    def _update_progress_tick(self, now: datetime) -> None:
        """Tick every minute while charging, so the estimated charge level moves."""
        if self.is_charge_now(now):
            if self._progress_tick is None:
                self._progress_tick = async_track_time_interval(
                    self.hass, self._handle_progress_tick, PROGRESS_INTERVAL
                )
        else:
            self._stop_progress_tick()

    @callback
    def _stop_progress_tick(self) -> None:
        if self._progress_tick is not None:
            self._progress_tick()
            self._progress_tick = None

    @callback
    def _handle_progress_tick(self, _now: datetime) -> None:
        # The tick is stopped at the end of each charging period and whenever
        # the plan changes (see _schedule_plan_boundaries).
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

    def progress(self, now: datetime | None = None) -> Progress | None:
        """The estimated charge level of the guest car, from the plan or the meter.

        EV Guest never sees the car's live charge level. Without an energy
        meter the estimate follows the plan; with one it follows the energy
        actually delivered. None without a plan (or for a plan from before
        0.9.0, which did not store its inputs).
        """
        measured = None
        if self.energy_entity:
            value = self.data.results.get(RESULT_MEASURED_ENERGY)
            measured = float(value) if isinstance(value, int | float) else None
        inputs = (self._plan_info or {}).get("inputs")
        return plan_progress(self._plan_segments, inputs, now or dt_util.now(), measured)

    # ------------------------------------------------------------------
    # Energy meter

    @callback
    def _handle_meter_update(self, event: Event[EventStateChangedData]) -> None:
        """Add what the charger's meter counted while the plan was active."""
        reading = meter_kwh(event.data["new_state"])
        if reading is None:
            return
        last, self._meter_last = self._meter_last, reading
        start, end = self.plan_start, self.plan_end
        if last is None or start is None or end is None or self._recorded:
            return
        now = dt_util.now()
        if not start <= now <= end + METER_GRACE:
            return
        step = reading - last
        if step <= 0 or step > MAX_METER_STEP_KWH:
            # A decrease is a meter reset; the next reading counts again.
            return
        energy = float(self.data.results.get(RESULT_MEASURED_ENERGY) or 0.0) + step
        cost = float(self.data.results.get(RESULT_MEASURED_COST) or 0.0)
        price = price_at(self.price_slots(now), now)
        if price is not None:
            cost += step * price
        self.data.results[RESULT_MEASURED_ENERGY] = round(energy, 3)
        self.data.results[RESULT_MEASURED_COST] = round(cost, 2)
        self._async_save_state()
        self.async_update_listeners()

    # ------------------------------------------------------------------
    # History

    @callback
    def _maybe_record(self, now: datetime | None = None, *, ended: bool = False) -> None:
        """Add the current plan to the history once it has finished.

        Normally that is a while after the plan ends, so late meter readings
        are included; ``ended`` records a finished plan right away (before it
        is replaced).
        """
        end = self.plan_end
        if self._recorded or self._plan_info is None or end is None:
            return
        now = now or dt_util.now()
        if now < end + (timedelta() if ended else METER_GRACE):
            return
        results = self.data.results
        entry = {
            **self._plan_info,
            "id": uuid4().hex,
            "start": self._plan_segments[0]["start"].isoformat(),
            "end": end.isoformat(),
            "measured_energy": results.get(RESULT_MEASURED_ENERGY),
            "measured_cost": results.get(RESULT_MEASURED_COST),
        }
        self.history = [entry, *self.history][:HISTORY_LIMIT]
        self._recorded = True
        self._async_save_state()

    async def async_delete_history(self, entry_id: str | None) -> None:
        """Delete one history entry, or all of them."""
        self.history = [] if entry_id is None else [entry for entry in self.history if entry.get("id") != entry_id]
        self._async_save_state()
        self.async_update_listeners()

    async def async_update_settings(self, changes: Mapping[str, Any]) -> None:
        """Change panel settings for billing guests."""
        self.settings.update({key: value for key, value in changes.items() if key in DEFAULT_SETTINGS})
        self._async_save_state()
        self.async_update_listeners()


# ----------------------------------------------------------------------
# Pure helpers (unit tested directly)


def meter_kwh(state: State | None) -> float | None:
    """An energy meter reading in kWh."""
    if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
        return None
    try:
        value = float(state.state)
    except ValueError:
        return None
    unit = state.attributes.get("unit_of_measurement")
    if unit == UnitOfEnergy.WATT_HOUR:
        return value / 1000
    if unit == UnitOfEnergy.MEGA_WATT_HOUR:
        return value * 1000
    return value


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
    return (value or time(7)).strftime("%H:%M")


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
