"""Tests for the websocket commands used by the panel."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from unittest.mock import patch

from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.ev_guest.api import BatteryLookupResult, VehicleLookupResult


async def _ws(client: Any, msg_id: int, **msg: Any) -> dict[str, Any]:
    await client.send_json({"id": msg_id, **msg})
    result: dict[str, Any] = await client.receive_json()
    return result


async def test_state_and_calculate(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client: WebSocketGenerator
) -> None:
    client = await hass_ws_client(hass)

    msg = await _ws(client, 1, type="ev_guest/state")
    assert msg["success"]
    state = msg["result"]
    assert state["entry_id"] == init_integration.entry_id
    assert state["entries"] == [{"entry_id": init_integration.entry_id, "title": "EV Guest"}]
    assert state["status"] == "ready"
    assert state["currency"] == "DKK"
    assert len(state["prices"]) == 11
    assert state["prices"][0]["end"] == "2026-04-09T21:00:00+02:00"
    assert state["inputs"]["charging_efficiency"] == 90
    assert state["config"] == {"price_entity": "sensor.energi_data_service", "energy_entity": None, "lookup": False}

    msg = await _ws(client, 2, type="ev_guest/calculate", entry_id=init_integration.entry_id)
    assert msg["success"]
    state = (await _ws(client, 3, type="ev_guest/state"))["result"]
    assert state["status"] == "planned"
    assert state["plan"]["cost"] == 19.25
    assert state["plan"]["segments"][0]["start"].startswith("2026-04-09T22:00")
    assert state["plan"]["info"]["energy"] == 51.33


async def test_set_inputs_and_preview(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client: WebSocketGenerator
) -> None:
    client = await hass_ws_client(hass)

    msg = await _ws(
        client,
        1,
        type="ev_guest/set_inputs",
        inputs={
            "license_plate": " ab 12345 ",
            "soc": 30,
            "charge_completion_time": "06:30",
            "charging_efficiency": 100,
        },
    )
    assert msg["success"]
    inputs = init_integration.runtime_data.data.inputs
    assert inputs["license_plate"] == "AB 12345"
    assert inputs["soc"] == 30
    assert inputs["charge_completion_time"] == "06:30"
    assert hass.states.get("number.ev_guest_charging_efficiency").state == "100.0"

    msg = await _ws(client, 2, type="ev_guest/preview", inputs={"soc": 70})
    assert msg["success"]
    preview = msg["result"]
    assert preview["minutes"] == 42
    assert preview["segments"][0]["start"].startswith("2026-04-10T00:00")
    # Nothing was stored.
    assert init_integration.runtime_data.data.inputs["soc"] == 30
    assert hass.states.get("sensor.ev_guest_status").state == "ready"

    msg = await _ws(client, 3, type="ev_guest/preview", inputs={"soc": 90})
    assert msg["result"] == {"error": "limit_not_above_soc"}

    msg = await _ws(client, 4, type="ev_guest/set_inputs", inputs={"soc": 120})
    assert not msg["success"]


async def test_errors_are_translated(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client: WebSocketGenerator
) -> None:
    client = await hass_ws_client(hass)

    msg = await _ws(client, 1, type="ev_guest/lookup")
    assert not msg["success"]
    assert msg["error"]["code"] == "license_plate_required"

    msg = await _ws(client, 2, type="ev_guest/state", entry_id="nope")
    assert msg["error"]["code"] == "entry_not_found"


async def test_lookup(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client: WebSocketGenerator
) -> None:
    hass.config_entries.async_update_entry(init_integration, data={**init_integration.data, "motorapi_api_key": "key"})
    init_integration.runtime_data.data.inputs["license_plate"] = "AB12345"
    vehicle = VehicleLookupResult("AB12345", None, "Kia", "EV6", "GT", 2024, "El", "MotorAPI", {})
    client = await hass_ws_client(hass)

    with (
        patch("custom_components.ev_guest.coordinator.async_lookup_vehicle", return_value=vehicle),
        patch(
            "custom_components.ev_guest.coordinator.async_lookup_battery_open_ev_data",
            return_value=BatteryLookupResult(74.0, "Open EV Data", 88.0, {}),
        ),
    ):
        msg = await _ws(client, 1, type="ev_guest/lookup")
    assert msg["success"]

    car = (await _ws(client, 2, type="ev_guest/state"))["result"]["car"]
    assert car["brand"] == "Kia"
    assert car["battery"] == 74.0
    assert car["match_score"] == 88.0


async def test_subscribe_sends_updates(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client: WebSocketGenerator
) -> None:
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "ev_guest/subscribe"})

    assert (await client.receive_json())["success"]
    first = await client.receive_json()
    assert first["type"] == "event"
    assert first["event"]["status"] == "ready"

    await init_integration.runtime_data.async_calculate()
    update = await client.receive_json()
    assert update["event"]["status"] == "planned"

    await hass.config_entries.async_reload(init_integration.entry_id)
    await hass.async_block_till_done()
    assert (await client.receive_json())["event"] == {"reload": True}


async def test_new_guest_history_and_settings(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
    now: datetime,
    freezer: FrozenDateTimeFactory,
) -> None:
    client = await hass_ws_client(hass)
    await _ws(client, 1, type="ev_guest/calculate")
    moment = now + timedelta(hours=8)
    freezer.move_to(moment)
    async_fire_time_changed(hass, moment)
    await hass.async_block_till_done()

    msg = await _ws(client, 2, type="ev_guest/new_guest")
    assert msg["success"]
    state = (await _ws(client, 3, type="ev_guest/state"))["result"]
    assert state["status"] == "ready"
    [entry] = state["history"]

    msg = await _ws(client, 4, type="ev_guest/settings", settings={"bill_price": 2.25, "payment_text": "MobilePay"})
    assert msg["success"]
    assert init_integration.runtime_data.settings == {"bill_price": 2.25, "payment_text": "MobilePay"}

    msg = await _ws(client, 5, type="ev_guest/delete_history", history_id=entry["id"])
    assert msg["success"]
    assert init_integration.runtime_data.history == []

    await _ws(client, 6, type="ev_guest/delete_history")
    assert init_integration.runtime_data.history == []
