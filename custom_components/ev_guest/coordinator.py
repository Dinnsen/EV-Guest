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
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from zoneinfo import ZoneInfo

from .api import (
    EVGuestLookupError,
    async_decode_vin_nhtsa,
    async_lookup_battery_open_ev_data,
    async_lookup_vehicle_motorapi,
)
from .const import (
    ATTR_LAST_CALCULATION,
    ATTR_LAST_LOOKUP,
    ATTR_LAST_SOURCE,
    ATTR_MODEL_YEAR,
    ATTR_STATUS,
    ATTR_VIN,
    CONF_CURRENCY,
    CONF_DURATION_FORMAT,
    CONF_MOTORAPI_KEY,
    CONF_PRICE_ENTITY,
    CONF_TIME_FORMAT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    DURATION_FORMAT_HM,
    DURATION_FORMAT_MINUTES,
    INPUT_BATTERY_CAPACITY,
    INPUT_CHARGE_COMPLETION_TIME,
    INPUT_CHARGE_LIMIT,
    INPUT_CHARGER_POWER,
    INPUT_LICENSE_PLATE,
    INPUT_SOC,
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


@dataclass
class EVGuestData:
    """Coordinator state."""

    inputs: dict[str, Any]
    results: dict[str, Any]


class EVGuestCoordinator(DataUpdateCoordinator[EVGuestData]):
    """Handle EV Guest data and calculations."""

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
        self.data = EVGuestData(
            inputs={
                INPUT_LICENSE_PLATE: "",
                INPUT_SOC: 20.0,
                INPUT_BATTERY_CAPACITY: 77.0,
                INPUT_CHARGER_POWER: 11.0,
                INPUT_CHARGE_LIMIT: 80.0,
                INPUT_CHARGE_COMPLETION_TIME: time(hour=7, minute=0),
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
            },
        )

    async def async_initialize(self) -> None:
        """Initialize listeners."""
        price_entity = self.config.get(CONF_PRICE_ENTITY, self.config_entry.data[CONF_PRICE_ENTITY])
        self._remove_price_listener = async_track_state_change_event(
            self.hass,
            [price_entity],
            self._handle_price_update,
        )
        await self.async_refresh()

    async def async_shutdown(self) -> None:
        """Shut down listeners."""
        if self._remove_price_listener:
            self._remove_price_listener()
            self._remove_price_listener = None

    @callback
    def _handle_price_update(self, event: Event) -> None:
        """Recalculate when the electricity price entity changes."""
        self.hass.async_create_task(self.async_calculate())

    async def _async_update_data(self) -> EVGuestData:
        """Refresh coordinator data."""
        return self.data

    async def async_set_input_value(self, key: str, value: Any) -> None:
        """Set an input value and update listeners."""
        self.data.inputs[key] = value
        self.async_update_listeners()

    async def async_lookup_car_data(self) -> None:
        """Look up vehicle details from external sources."""
        plate = self.data.inputs.get(INPUT_LICENSE_PLATE, "")
        if not plate:
            self.data.results[RESULT_STATUS] = "License plate is required"
            self.async_update_listeners()
            return

        api_key = self.config.get(CONF_MOTORAPI_KEY, self.config_entry.data.get(CONF_MOTORAPI_KEY))
        try:
            vehicle = await async_lookup_vehicle_motorapi(self.session, plate, api_key)
        except EVGuestLookupError as err:
            self.data.results[RESULT_STATUS] = f"Lookup failed: {err}"
            self.async_update_listeners()
            return

        vin = vehicle.get("vin")
        brand = vehicle.get("brand")
        model = vehicle.get("model")
        variant = vehicle.get("variant")
        model_year = vehicle.get("model_year")

        nhtsa = {}
        if vin:
            try:
                normalized_year = int(model_year) if model_year is not None else None
            except (TypeError, ValueError):
                normalized_year = None
            nhtsa = await async_decode_vin_nhtsa(self.session, vin, normalized_year)

        if not brand:
            brand = nhtsa.get("brand")
        if not model:
            model = nhtsa.get("model")
        if not variant:
            variant = nhtsa.get("variant")
        if not model_year:
            model_year = nhtsa.get("model_year")

        battery_match = await async_lookup_battery_open_ev_data(
            self.session,
            brand=brand,
            model=model,
            variant=variant,
            model_year=int(model_year) if str(model_year).isdigit() else None,
        )
        battery_capacity = battery_match.get("battery_capacity")

        self.data.results[RESULT_CAR_BRAND] = brand
        self.data.results[RESULT_CAR_MODEL] = model
        self.data.results[RESULT_CAR_VARIANT] = variant
        self.data.results[RESULT_CAR_BATTERY_CAPACITY] = battery_capacity
        self.data.results[ATTR_LAST_LOOKUP] = self._local_now().isoformat()
        self.data.results[ATTR_LAST_SOURCE] = ", ".join(
            source for source in [vehicle.get("source"), nhtsa.get("source") if nhtsa else None, battery_match.get("source") if battery_match else None] if source
        ) or None
        self.data.results[ATTR_VIN] = vin
        self.data.results[ATTR_MODEL_YEAR] = model_year

        if battery_capacity is not None:
            self.data.inputs[INPUT_BATTERY_CAPACITY] = float(battery_capacity)

        if battery_capacity is not None:
            self.data.results[RESULT_STATUS] = "Vehicle data fetched"
        else:
            self.data.results[RESULT_STATUS] = "Vehicle data fetched, but battery data was not matched"
        self.async_update_listeners()

    async def async_calculate(self) -> None:
        """Calculate the cheapest charge schedule."""
        try:
            calculation = self._calculate_schedule()
        except ValueError as err:
            self.data.results[RESULT_STATUS] = str(err)
            self.async_update_listeners()
            return
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("Unexpected calculation error")
            self.data.results[RESULT_STATUS] = f"Calculation failed: {err}"
            self.async_update_listeners()
            return

        self.data.results.update(calculation)
        self.data.results[ATTR_LAST_CALCULATION] = self._local_now().isoformat()
        self.data.results[RESULT_STATUS] = "Calculation complete"
        self.async_update_listeners()

    def _calculate_schedule(self) -> dict[str, Any]:
        soc = float(self.data.inputs[INPUT_SOC])
        battery_capacity = float(self.data.inputs[INPUT_BATTERY_CAPACITY])
        charger_power = float(self.data.inputs[INPUT_CHARGER_POWER])
        charge_limit = float(self.data.inputs[INPUT_CHARGE_LIMIT])
        completion_time: time = self.data.inputs[INPUT_CHARGE_COMPLETION_TIME]

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

        speed_pct_per_hour = (charger_power / battery_capacity) * 100
        energy_needed_kwh = battery_capacity * ((charge_limit - soc) / 100)
        charge_minutes = ceil((energy_needed_kwh / charger_power) * 60)
        required_hours = charge_minutes / 60

        prices = self._extract_price_slots()
        if not prices:
            raise ValueError("No usable price data available from selected price sensor")

        now = self._local_now()
        deadline = self._resolve_deadline(now, completion_time)

        eligible_slots = [slot for slot in prices if now <= slot[0] < deadline]
        if not eligible_slots:
            raise ValueError("No price slots available before completion time")

        slot_count = ceil(required_hours)
        if len(eligible_slots) < slot_count:
            raise ValueError("Not enough hourly price slots before completion time")

        best_window: list[tuple[datetime, float]] | None = None
        best_cost: float | None = None

        for index in range(0, len(eligible_slots) - slot_count + 1):
            window = eligible_slots[index : index + slot_count]
            window_end = window[-1][0] + timedelta(hours=1)
            if window_end > deadline:
                continue

            cost = self._estimate_cost(window, energy_needed_kwh, required_hours)
            if best_cost is None or cost < best_cost:
                best_cost = cost
                best_window = window

        if best_window is None or best_cost is None:
            raise ValueError("No valid charging window found before completion time")

        start = best_window[0][0]
        end = start + timedelta(minutes=charge_minutes)

        return {
            RESULT_CHARGING_SPEED: round(speed_pct_per_hour, 2),
            RESULT_CHARGE_START_TIME: self._format_datetime(start),
            RESULT_CHARGE_END_TIME: self._format_datetime(end),
            RESULT_CHARGE_TIME: self._format_duration(charge_minutes),
            RESULT_CHARGE_COSTS: round(best_cost, 2),
        }

    def _estimate_cost(
        self,
        window: list[tuple[datetime, float]],
        energy_needed_kwh: float,
        required_hours: float,
    ) -> float:
        remaining_energy = energy_needed_kwh
        total_cost = 0.0
        charger_power = float(self.data.inputs[INPUT_CHARGER_POWER])

        for hour_start, price in window:
            del hour_start
            energy_this_hour = min(charger_power, remaining_energy)
            total_cost += energy_this_hour * float(price)
            remaining_energy -= energy_this_hour
            if remaining_energy <= 0:
                break

        full_hours = int(required_hours)
        partial_hour_fraction = required_hours - full_hours
        if partial_hour_fraction > 0 and len(window) > full_hours:
            last_hour_price = float(window[full_hours][1])
            overcount_energy = charger_power * (1 - partial_hour_fraction)
            total_cost -= overcount_energy * last_hour_price

        return total_cost

    def _extract_price_slots(self) -> list[tuple[datetime, float]]:
        entity_id = self.config.get(CONF_PRICE_ENTITY, self.config_entry.data[CONF_PRICE_ENTITY])
        state = self.hass.states.get(entity_id)
        if state is None or state.state in {STATE_UNKNOWN, STATE_UNAVAILABLE}:
            raise ValueError("Selected electricity price sensor is unavailable")

        attrs = state.attributes
        timezone = self.hass.config.time_zone or "Europe/Copenhagen"
        tzinfo = ZoneInfo(timezone)

        slots: list[tuple[datetime, float]] = []

        def parse_hourly_dicts(items: list[dict[str, Any]]) -> None:
            for item in items:
                hour_raw = item.get("hour")
                price = item.get("price")
                if hour_raw is None or price is None:
                    continue
                dt = datetime.fromisoformat(hour_raw)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=tzinfo)
                else:
                    dt = dt.astimezone(tzinfo)
                slots.append((dt, float(price)))

        if isinstance(attrs.get("raw_today"), list):
            parse_hourly_dicts(attrs["raw_today"])
        if isinstance(attrs.get("raw_tomorrow"), list):
            parse_hourly_dicts(attrs["raw_tomorrow"])
        if isinstance(attrs.get("forecast"), list):
            parse_hourly_dicts(attrs["forecast"])

        if not slots and isinstance(attrs.get("today"), list):
            base = self._local_now().replace(hour=0, minute=0, second=0, microsecond=0)
            for index, price in enumerate(attrs["today"]):
                slots.append((base + timedelta(hours=index), float(price)))
            if isinstance(attrs.get("tomorrow"), list):
                tomorrow_base = base + timedelta(days=1)
                for index, price in enumerate(attrs["tomorrow"]):
                    slots.append((tomorrow_base + timedelta(hours=index), float(price)))

        deduped: dict[datetime, float] = {}
        for dt, price in sorted(slots, key=lambda item: item[0]):
            deduped[dt] = price

        return sorted(deduped.items(), key=lambda item: item[0])

    def _resolve_deadline(self, now: datetime, completion_time: time) -> datetime:
        deadline = now.replace(
            hour=completion_time.hour,
            minute=completion_time.minute,
            second=0,
            microsecond=0,
        )
        if deadline <= now:
            deadline += timedelta(days=1)
        return deadline

    def _format_datetime(self, value: datetime) -> str:
        if self.config.get(CONF_TIME_FORMAT, self.config_entry.data[CONF_TIME_FORMAT]) == TIME_FORMAT_12H:
            return value.strftime("%I:%M %p")
        return value.strftime("%H:%M")

    def _format_duration(self, total_minutes: int) -> str | int:
        if self.config.get(CONF_DURATION_FORMAT, self.config_entry.data[CONF_DURATION_FORMAT]) == DURATION_FORMAT_MINUTES:
            return total_minutes
        hours, minutes = divmod(total_minutes, 60)
        return f"{hours}h {minutes:02d}m"

    def _local_now(self) -> datetime:
        timezone = self.hass.config.time_zone or "Europe/Copenhagen"
        return datetime.now(ZoneInfo(timezone))

    @property
    def config(self) -> dict[str, Any]:
        """Return merged config and options."""
        return {**self.config_entry.data, **self.config_entry.options}

    @property
    def currency(self) -> str:
        return self.config.get(CONF_CURRENCY, self.config_entry.data[CONF_CURRENCY])
