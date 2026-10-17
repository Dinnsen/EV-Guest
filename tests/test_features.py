"""Tests for charging efficiency, new guest, history and the energy meter."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.ev_guest import api
from custom_components.ev_guest.const import CONF_CURRENCY, CONF_ENERGY_ENTITY, DOMAIN, STORAGE_KEY
from custom_components.ev_guest.diagnostics import async_get_config_entry_diagnostics

from .conftest import CONTINUOUS_PRICES, set_prices

METER = "sensor.charger_energy"
STATUS = "sensor.ev_guest_status"
PLATE = "text.ev_guest_license_plate"


async def _press(hass: HomeAssistant, key: str) -> None:
    await hass.services.async_call("button", "press", {ATTR_ENTITY_ID: f"button.ev_guest_{key}"}, blocking=True)
    await hass.async_block_till_done()


async def _move(hass: HomeAssistant, freezer: FrozenDateTimeFactory, moment: datetime) -> None:
    freezer.move_to(moment)
    async_fire_time_changed(hass, moment)
    await hass.async_block_till_done()


def _value(hass: HomeAssistant, entity_id: str) -> float:
    state = hass.states.get(entity_id)
    assert state is not None, entity_id
    return float(state.state)


async def test_efficiency_changes_cost_and_time(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    await hass.services.async_call(
        "number", "set_value", {ATTR_ENTITY_ID: "number.ev_guest_charging_efficiency", "value": 100}, blocking=True
    )
    await _press(hass, "calculate")

    assert hass.states.get("sensor.ev_guest_charge_time").state == "252"
    assert _value(hass, "sensor.ev_guest_charge_costs") == pytest.approx(14.63, rel=1e-3)
    assert _value(hass, "sensor.ev_guest_energy_needed") == pytest.approx(46.2)
    savings = hass.states.get("sensor.ev_guest_savings")
    assert savings is not None
    assert savings.attributes["charge_now_cost"] == pytest.approx(11 * (1.8 + 1.5 + 0.4 + 0.3 + 0.2 * 0.2), rel=1e-3)
    assert savings.attributes["unit_of_measurement"] == "DKK"


async def test_new_guest_clears_guest_and_plan(
    hass: HomeAssistant, init_integration: MockConfigEntry, now: datetime, freezer: FrozenDateTimeFactory
) -> None:
    await hass.services.async_call("text", "set_value", {ATTR_ENTITY_ID: PLATE, "value": "AB12345"}, blocking=True)
    init_integration.runtime_data.data.results["car_brand"] = "Tesla"
    await _press(hass, "calculate")
    # The plan ended at 02:40; it is normally added to the history at 02:50.
    await _move(hass, freezer, now + timedelta(hours=6, minutes=45))

    await hass.services.async_call(DOMAIN, "new_guest", {}, blocking=True)

    coordinator = init_integration.runtime_data
    assert hass.states.get(STATUS).state == "ready"
    assert hass.states.get(PLATE).state == ""
    assert coordinator.data.results["car_brand"] is None
    assert hass.states.get("sensor.ev_guest_charge_costs").state == "unknown"
    # The finished plan was kept right away.
    [entry] = coordinator.history
    assert entry["plate"] == "AB12345"
    assert entry["car"] == "Tesla"


async def test_unfinished_plan_is_not_added_to_history(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    await _press(hass, "calculate")
    await _press(hass, "new_guest")

    assert init_integration.runtime_data.history == []


async def test_replacing_a_finished_plan_records_it(
    hass: HomeAssistant, init_integration: MockConfigEntry, now: datetime, freezer: FrozenDateTimeFactory
) -> None:
    await _press(hass, "calculate")
    await _move(hass, freezer, now + timedelta(hours=6, minutes=45))
    set_prices(hass, now + timedelta(hours=7), CONTINUOUS_PRICES)
    await hass.services.async_call(
        "switch", "turn_off", {ATTR_ENTITY_ID: "switch.ev_guest_use_charge_completion_time"}, blocking=True
    )

    await _press(hass, "calculate")

    assert len(init_integration.runtime_data.history) == 1
    assert hass.states.get(STATUS).state == "planned"


async def test_history_and_settings_are_stored(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    hass_storage: dict[str, Any],
    now: datetime,
    freezer: FrozenDateTimeFactory,
) -> None:
    coordinator = init_integration.runtime_data
    await _press(hass, "calculate")
    await _move(hass, freezer, now + timedelta(hours=8))
    await coordinator.async_update_settings({"bill_price": 2.5, "payment_text": "MobilePay 1234", "other": 1})
    await _move(hass, freezer, now + timedelta(hours=8, seconds=5))

    stored = hass_storage[STORAGE_KEY.format(entry_id=init_integration.entry_id)]["data"]
    assert len(stored["history"]) == 1
    assert stored["settings"] == {"bill_price": 2.5, "payment_text": "MobilePay 1234"}

    await hass.config_entries.async_reload(init_integration.entry_id)
    await hass.async_block_till_done()
    coordinator = init_integration.runtime_data
    assert len(coordinator.history) == 1
    assert coordinator.settings["payment_text"] == "MobilePay 1234"

    await coordinator.async_delete_history("unknown")
    assert len(coordinator.history) == 1
    await coordinator.async_delete_history(coordinator.history[0]["id"])
    assert coordinator.history == []


async def test_plan_finished_while_stopped_is_recorded_on_start(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    now: datetime,
    freezer: FrozenDateTimeFactory,
) -> None:
    await _press(hass, "calculate")
    await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()
    freezer.move_to(now + timedelta(hours=9))

    assert await hass.config_entries.async_setup(init_integration.entry_id)
    await hass.async_block_till_done()

    assert len(init_integration.runtime_data.history) == 1


@pytest.fixture
async def metered_integration(
    hass: HomeAssistant, now: datetime, mock_config_entry: MockConfigEntry
) -> MockConfigEntry:
    """EV Guest with the charger's energy meter."""
    hass.states.async_set(METER, "1000.0", {"unit_of_measurement": "kWh", "device_class": "energy"})
    set_prices(hass, now, CONTINUOUS_PRICES)
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry, options={**mock_config_entry.options, CONF_ENERGY_ENTITY: METER}
    )
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry


async def test_meter_measures_energy_and_cost_during_the_plan(
    hass: HomeAssistant, metered_integration: MockConfigEntry, now: datetime, freezer: FrozenDateTimeFactory
) -> None:
    await _press(hass, "calculate")
    assert _value(hass, "sensor.ev_guest_measured_energy") == 0

    # Before the plan starts: not counted.
    hass.states.async_set(METER, "1003.0", {"unit_of_measurement": "kWh"})
    await hass.async_block_till_done()

    await _move(hass, freezer, now + timedelta(hours=2, minutes=30))  # 22:30, price 0.40
    hass.states.async_set(METER, "1008.0", {"unit_of_measurement": "kWh"})
    await hass.async_block_till_done()
    await _move(hass, freezer, now + timedelta(hours=3, minutes=30))  # 23:30, price 0.30
    hass.states.async_set(METER, "1018.0", {"unit_of_measurement": "kWh"})
    # A glitch and a reset are ignored.
    hass.states.async_set(METER, "unavailable")
    hass.states.async_set(METER, "5.0", {"unit_of_measurement": "kWh"})
    hass.states.async_set(METER, "500.0", {"unit_of_measurement": "kWh"})
    await hass.async_block_till_done()

    assert _value(hass, "sensor.ev_guest_measured_energy") == pytest.approx(15)
    assert _value(hass, "sensor.ev_guest_measured_cost") == pytest.approx(5 * 0.4 + 10 * 0.3)

    await _move(hass, freezer, now + timedelta(hours=7))
    [entry] = metered_integration.runtime_data.history
    assert entry["measured_energy"] == pytest.approx(15)

    # After the plan: not counted.
    hass.states.async_set(METER, "510.0", {"unit_of_measurement": "kWh"})
    await hass.async_block_till_done()
    assert _value(hass, "sensor.ev_guest_measured_energy") == pytest.approx(15)


async def test_meter_entities_only_with_a_meter(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    assert hass.states.get("sensor.ev_guest_measured_energy") is None


async def test_options_flow_sets_energy_meter(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    hass.states.async_set(METER, "1", {"unit_of_measurement": "kWh", "device_class": "energy"})
    result = await hass.config_entries.options.async_init(init_integration.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_CURRENCY: "DKK", CONF_ENERGY_ENTITY: METER}
    )
    await hass.async_block_till_done()

    assert init_integration.options == {CONF_CURRENCY: "DKK", CONF_ENERGY_ENTITY: METER}
    assert hass.states.get("sensor.ev_guest_measured_energy") is not None


async def test_diagnostics_redact_history_plates(
    hass: HomeAssistant, init_integration: MockConfigEntry, now: datetime, freezer: FrozenDateTimeFactory
) -> None:
    await hass.services.async_call("text", "set_value", {ATTR_ENTITY_ID: PLATE, "value": "AB12345"}, blocking=True)
    await _press(hass, "calculate")
    await _move(hass, freezer, now + timedelta(hours=8))

    diagnostics = await async_get_config_entry_diagnostics(hass, init_integration)

    assert diagnostics["history"][0]["plate"] == "**REDACTED**"
    assert diagnostics["plan_info"]["plate"] == "**REDACTED**"


async def test_open_ev_data_is_cached(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    dataset = [{"brand": "Tesla", "model": "Model 3", "battery_capacity": 75}]
    aioclient_mock.get(api.OPEN_EV_DATA_URL, json=dataset)

    cache: dict[str, Any] = {}
    client = async_get_clientsession(hass)
    first = await api.async_lookup_battery_open_ev_data(client, "Tesla", "Model 3", None, None, cache=cache)
    second = await api.async_lookup_battery_open_ev_data(client, "Tesla", "Model 3", None, None, cache=cache)

    assert first.battery_capacity == second.battery_capacity == 75
    assert aioclient_mock.call_count == 1
