"""Websocket commands used by the EV Guest panel."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import functools
from typing import Any

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_AVERAGE_PRICE,
    ATTR_CHARGE_NOW_COST,
    ATTR_LAST_CALCULATION,
    ATTR_LAST_LOOKUP,
    ATTR_MATCH_SCORE,
    ATTR_MODEL_YEAR,
    ATTR_PLAN_MODE,
    DOMAIN,
    INPUT_BATTERY_CAPACITY,
    INPUT_CHARGE_COMPLETION_TIME,
    INPUT_CHARGE_LIMIT,
    INPUT_CHARGER_POWER,
    INPUT_CHARGING_EFFICIENCY,
    INPUT_CONTINUOUS_CHARGING_PREFERRED,
    INPUT_LICENSE_PLATE,
    INPUT_SOC,
    INPUT_USE_COMPLETION_TIME,
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
)
from .coordinator import EVGuestConfigEntry, EVGuestCoordinator, PlanError, serialize_segments
from .schema import vol

ENTRY = vol.Optional("entry_id")

INPUT_SCHEMA = vol.Schema(
    {
        vol.Optional(INPUT_LICENSE_PLATE): vol.All(cv.string, vol.Length(max=16)),
        vol.Optional(INPUT_SOC): vol.All(vol.Coerce(float), vol.Range(min=0, max=100)),
        vol.Optional(INPUT_CHARGE_LIMIT): vol.All(vol.Coerce(float), vol.Range(min=0, max=100)),
        vol.Optional(INPUT_BATTERY_CAPACITY): vol.All(vol.Coerce(float), vol.Range(min=1, max=300)),
        vol.Optional(INPUT_CHARGER_POWER): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=350)),
        vol.Optional(INPUT_CHARGING_EFFICIENCY): vol.All(vol.Coerce(float), vol.Range(min=50, max=100)),
        vol.Optional(INPUT_CHARGE_COMPLETION_TIME): cv.time,
        vol.Optional(INPUT_USE_COMPLETION_TIME): cv.boolean,
        vol.Optional(INPUT_CONTINUOUS_CHARGING_PREFERRED): cv.boolean,
    }
)
SETTINGS_SCHEMA = vol.Schema(
    {
        vol.Optional("bill_price"): vol.Any(None, vol.All(vol.Coerce(float), vol.Range(min=0))),
        vol.Optional("payment_text"): vol.All(cv.string, vol.Length(max=200)),
    }
)

type _Handler = Callable[[HomeAssistant, websocket_api.ActiveConnection, dict[str, Any]], Awaitable[None]]


def _coordinator(hass: HomeAssistant, msg: dict[str, Any]) -> EVGuestCoordinator:
    entries: list[EVGuestConfigEntry] = hass.config_entries.async_loaded_entries(DOMAIN)
    if entry_id := msg.get("entry_id"):
        entries = [entry for entry in entries if entry.entry_id == entry_id]
    if not entries:
        raise ServiceValidationError(translation_domain=DOMAIN, translation_key="entry_not_found")
    return entries[0].runtime_data


def _errors(func: _Handler) -> _Handler:
    """Send translated errors back to the panel instead of failing the command."""

    @functools.wraps(func)
    async def wrapper(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
        try:
            await func(hass, connection, msg)
        except HomeAssistantError as err:
            connection.send_error(msg["id"], err.translation_key or "unknown", str(err))

    return wrapper


def panel_state(hass: HomeAssistant, coordinator: EVGuestCoordinator) -> dict[str, Any]:
    """Everything the panel shows, for one EV Guest."""
    now = dt_util.now()
    results = coordinator.data.results
    inputs = dict(coordinator.data.inputs)
    slots = coordinator.visible_slots(coordinator.price_slots(now))
    entries: list[EVGuestConfigEntry] = hass.config_entries.async_loaded_entries(DOMAIN)
    return {
        "entry_id": coordinator.config_entry.entry_id,
        "entries": [{"entry_id": entry.entry_id, "title": entry.title} for entry in entries],
        "title": coordinator.config_entry.title,
        "now": now.isoformat(),
        "currency": coordinator.currency,
        "status": coordinator.status(now),
        "error": coordinator.error,
        "error_detail": coordinator.error_detail,
        "charge_now": coordinator.is_charge_now(now),
        "plan_locked": coordinator.is_plan_locked(now),
        "inputs": inputs,
        "car": {
            "brand": results.get(RESULT_CAR_BRAND),
            "model": results.get(RESULT_CAR_MODEL),
            "variant": results.get(RESULT_CAR_VARIANT),
            "battery": results.get(RESULT_CAR_BATTERY_CAPACITY),
            "model_year": results.get(ATTR_MODEL_YEAR),
            "match_score": results.get(ATTR_MATCH_SCORE),
            "looked_up": results.get(ATTR_LAST_LOOKUP),
        },
        "plan": {
            "segments": serialize_segments(coordinator.plan_segments),
            "mode": results.get(ATTR_PLAN_MODE),
            "speed": results.get(RESULT_CHARGING_SPEED),
            "minutes": results.get(RESULT_CHARGE_TIME),
            "cost": results.get(RESULT_CHARGE_COSTS),
            "energy": results.get(RESULT_ENERGY),
            "savings": results.get(RESULT_SAVINGS),
            "charge_now_cost": results.get(ATTR_CHARGE_NOW_COST),
            "average_price": results.get(ATTR_AVERAGE_PRICE),
            "calculated": results.get(ATTR_LAST_CALCULATION),
            "info": coordinator.plan_info,
            "measured_energy": results.get(RESULT_MEASURED_ENERGY),
            "measured_cost": results.get(RESULT_MEASURED_COST),
        },
        "prices": [
            {"start": slot.start.isoformat(), "end": slot.end.isoformat(), "price": slot.price} for slot in slots
        ],
        "config": {
            "price_entity": coordinator.price_entity,
            "energy_entity": coordinator.energy_entity,
            "lookup": coordinator.has_motorapi_key,
        },
        "service_health": dict(coordinator.data.service_health),
        "history": coordinator.history,
        "settings": coordinator.settings,
    }


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/subscribe", ENTRY: str})
@websocket_api.async_response
@_errors
async def ws_subscribe(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Send the panel state now and whenever it changes."""
    coordinator = _coordinator(hass, msg)

    @callback
    def send() -> None:
        connection.send_message(websocket_api.event_message(msg["id"], panel_state(hass, coordinator)))

    @callback
    def reloaded() -> None:
        # Options changes reload the entry; the panel then subscribes again.
        connection.send_message(websocket_api.event_message(msg["id"], {"reload": True}))

    connection.subscriptions[msg["id"]] = coordinator.async_add_listener(send)
    coordinator.config_entry.async_on_unload(reloaded)
    connection.send_result(msg["id"])
    send()


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/state", ENTRY: str})
@websocket_api.async_response
@_errors
async def ws_state(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    connection.send_result(msg["id"], panel_state(hass, _coordinator(hass, msg)))


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/set_inputs", ENTRY: str, vol.Required("inputs"): INPUT_SCHEMA}
)
@websocket_api.async_response
@_errors
async def ws_set_inputs(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    coordinator = _coordinator(hass, msg)
    for key, value in msg["inputs"].items():
        if key == INPUT_LICENSE_PLATE:
            value = str(value).strip().upper()
        await coordinator.async_set_input_value(key, value)
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/preview", ENTRY: str, vol.Optional("inputs", default={}): INPUT_SCHEMA}
)
@websocket_api.async_response
@_errors
async def ws_preview(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """A plan for inputs being changed, without storing anything."""
    coordinator = _coordinator(hass, msg)
    try:
        plan, _slots = coordinator.make_plan({**coordinator.data.inputs, **msg["inputs"]})
    except PlanError as err:
        connection.send_result(msg["id"], {"error": err.key})
        return
    connection.send_result(
        msg["id"],
        {
            "segments": serialize_segments(plan.segments),
            "mode": plan.mode,
            "cost": round(plan.cost, 2),
            "energy": round(plan.need.grid_kwh, 2),
            "minutes": plan.need.minutes,
            "speed": round(plan.need.speed_pct_per_hour, 1),
            "savings": None if plan.savings is None else round(plan.savings, 2),
            "charge_now_cost": None if plan.charge_now_cost is None else round(plan.charge_now_cost, 2),
        },
    )


def _action(name: str, run: Callable[[EVGuestCoordinator], Awaitable[None]]) -> Any:
    @websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/{name}", ENTRY: str})
    @websocket_api.async_response
    @_errors
    async def handler(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
        await run(_coordinator(hass, msg))
        connection.send_result(msg["id"])

    return handler


ws_lookup = _action("lookup", lambda coordinator: coordinator.async_lookup_car_data())
ws_calculate = _action("calculate", lambda coordinator: coordinator.async_calculate())
ws_new_guest = _action("new_guest", lambda coordinator: coordinator.async_new_guest())


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/delete_history", ENTRY: str, vol.Optional("history_id"): vol.Any(None, str)}
)
@websocket_api.async_response
@_errors
async def ws_delete_history(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Delete one history entry, or all without ``history_id``."""
    await _coordinator(hass, msg).async_delete_history(msg.get("history_id"))
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/settings", ENTRY: str, vol.Required("settings"): SETTINGS_SCHEMA}
)
@websocket_api.async_response
@_errors
async def ws_settings(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    await _coordinator(hass, msg).async_update_settings(msg["settings"])
    connection.send_result(msg["id"])


@callback
def async_register_websocket(hass: HomeAssistant) -> None:
    """Register the panel's commands."""
    for command in (
        ws_subscribe,
        ws_state,
        ws_set_inputs,
        ws_preview,
        ws_lookup,
        ws_calculate,
        ws_new_guest,
        ws_delete_history,
        ws_settings,
    ):
        websocket_api.async_register_command(hass, command)
