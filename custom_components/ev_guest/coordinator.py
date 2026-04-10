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
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .api import (
    EVGuestAuthError,
    EVGuestLookupError,
    VehicleLookupResult,
    async_decode_vin_nhtsa,
    async_lookup_battery_open_ev_data,
    async_lookup_vehicle_motorapi,
    async_validate_motorapi_key,
)
from .const import (
    ATTR_FUEL_TYPE,
    ATTR_LAST_CALCULATION,
    ATTR_LAST_LOOKUP,
    ATTR_LAST_SOURCE,
    ATTR_MATCH_SCORE,
    ATTR_MODEL_YEAR,
    ATTR_VIN,
    CONF_CURRENCY,
    CONF_DURATION_FORMAT,
    CONF_MOTORAPI_KEY,
    CONF_PRICE_ENTITY,
    CONF_TIME_FORMAT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    DURATION_FORMAT_HM,
    INPUT_BATTERY_CAPACITY,
    INPUT_CHARGE_COMPLETION_TIME,
    INPUT_CHARGE_LIMIT,
    INPUT_CHARGER_POWER,
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
        self.data = EVGuestData(
            inputs={
                INPUT_LICENSE_PLATE: "",
                INPUT_SOC: 20.0,
                INPUT_BATTERY_CAPACITY: 77.0,
                INPUT_CHARGER_POWER: 11.0,
                INPUT_CHARGE_LIMIT: 80.0,
                INPUT_CHARGE_COMPLETION_TIME: "07:00",
                INPUT_USE_COMPLETION_TIME: True,
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
            },
            service_health={"motorapi": True, "nhtsa": True, "open_ev_data": True},
        )

    @property
    def config(self) -> dict[str, Any]:
        return {**self.config_entry.data, **self.config_entry.options}

    @property
    def currency(self) -> str:
        return self.config.get(CONF_CURRENCY, "DKK")

    async def async_initialize(self) -> None:
        await self._async_validate_setup()
        price_entity = self.config[CONF_PRICE_ENTITY]
        self._remove_price_listener = async_track_state_change_event(
            self.hass,
            [price_entity],
            self._handle_price_update,
        )
        await self.async_refresh()

    async def _async_validate_setup(self) -> None:
        try:
            await async_validate_motorapi_key(self.session, self.config[CONF_MOTORAPI_KEY])
            self._set_service_health("motorapi", True)
        except EVGuestAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except EVGuestLookupError as err:
            raise ConfigEntryError(str(err)) from err

    async def async_shutdown(self) -> None:
        if self._remove_price_listener:
            self._remove_price_listener()
            self._remove_price_listener = None

    @callback
    def _handle_price_update(self, event: Event) -> None:
        self.hass.async_create_task(self.async_calculate())

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

        try:
            motor = await async_lookup_vehicle_motorapi(self.session, plate, self.config[CONF_MOTORAPI_KEY])
            self._set_service_health("motorapi", True)
        except EVGuestAuthError as err:
            self._set_service_health("motorapi", False)
            raise ConfigEntryAuthFailed(str(err)) from err
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
        self._set_service_health("open_ev_data", battery.raw is not None or battery.match_score is None)

        self.data.results[RESULT_CAR_BRAND] = normalized.brand
        self.data.results[RESULT_CAR_MODEL] = normalized.model
        self.data.results[RESULT_CAR_VARIANT] = normalized.variant
        self.data.results[ATTR_VIN] = normalized.vin
        self.data.results[ATTR_MODEL_YEAR] = normalized.model_year
        self.data.results[ATTR_FUEL_TYPE] = normalized.fuel_type
        self.data.results[ATTR_LAST_LOOKUP] = self._local_now().isoformat()
        self.data.results[ATTR_LAST_SOURCE] = ", ".join(
            source for source in [motor.source, decoded.source if decoded else None, battery.source] if source
        )
        self.data.results[ATTR_MATCH_SCORE] = battery.match_score

        if battery.battery_capacity is not None:
            self.data.results[RESULT_CAR_BATTERY_CAPACITY] = round(battery.battery_capacity, 1)
            self.data.inputs[INPUT_BATTERY_CAPACITY] = round(battery.battery_capacity, 1)
            self.data.results[RESULT_STATUS] = "Car data loaded"
        else:
            self.data.results[RESULT_STATUS] = "Car data loaded, battery match not confident"

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
        self.async_update_listeners()

    def _calculate_schedule(self) -> dict[str, Any]:
        soc = float(self.data.inputs[INPUT_SOC])
        battery_capacity = float(self.data.inputs[INPUT_BATTERY_CAPACITY])
        charger_power = float(self.data.inputs[INPUT_CHARGER_POWER])
        charge_limit = float(self.data.inputs[INPUT_CHARGE_LIMIT])
        use_completion_time = bool(self.data.inputs.get(INPUT_USE_COMPLETION_TIME, True))
        completion_time = self._parse_completion_time(self.data.inputs.get(INPUT_CHARGE_COMPLETION_TIME))

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

        prices = self._extract_price_slots()
        if not prices:
            raise ValueError("No usable price data available from selected price sensor")

        now = self._local_now()
        valid_prices = [slot for slot in prices if now <= slot[0]]
        hours_needed = ceil(required_hours)
        completion_dt = None
        if use_completion_time:
            completion_dt = self._next_completion_datetime(now, completion_time)
            valid_prices = [slot for slot in valid_prices if slot[0] < completion_dt]
            if len(valid_prices) < hours_needed:
                raise ValueError("Not enough future hourly prices available before completion time")
        if len(valid_prices) < hours_needed:
            raise ValueError("Not enough future hourly prices available")

        cheapest_window = None
        for index in range(0, len(valid_prices) - hours_needed + 1):
            window = valid_prices[index : index + hours_needed]
            if use_completion_time and completion_dt and window[-1][0] + timedelta(hours=1) > completion_dt:
                continue
            cost = self._window_cost(window, energy_needed_kwh, required_hours)
            if cheapest_window is None or cost < cheapest_window["cost"]:
                cheapest_window = {
                    "start": window[0][0],
                    "end": window[0][0] + timedelta(minutes=charge_minutes),
                    "cost": cost,
                }

        if cheapest_window is None:
            raise ValueError("No valid charging window found")

        return {
            RESULT_CHARGING_SPEED: round(speed_pct_per_hour, 1),
            RESULT_CHARGE_START_TIME: self._format_datetime(cheapest_window["start"]),
            RESULT_CHARGE_END_TIME: self._format_datetime(cheapest_window["end"]),
            RESULT_CHARGE_TIME: self._format_duration(charge_minutes),
            RESULT_CHARGE_COSTS: round(cheapest_window["cost"], 2),
        }

    def _extract_price_slots(self) -> list[tuple[datetime, float]]:
        state = self.hass.states.get(self.config[CONF_PRICE_ENTITY])
        if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return []

        slots: list[tuple[datetime, float]] = []
        attrs = state.attributes

        for key in ("raw_today", "raw_tomorrow", "forecast"):
            for row in attrs.get(key, []):
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
