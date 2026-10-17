"""Tests for the guest session and the charger control sensor.

The rule under test: EV Guest only holds the charger during a guest session,
and a session always ends by itself, so a charger automation never blocks
the owner's own car because EV Guest thinks a guest is still there.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from freezegun.api import FrozenDateTimeFactory
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed

from custom_components.ev_guest.const import CONF_CURRENCY, CONF_ENERGY_ENTITY, CONF_VEHICLE_ENTITY
from custom_components.ev_guest.diagnostics import async_get_config_entry_diagnostics
from custom_components.ev_guest.websocket import panel_state

from .conftest import CONTINUOUS_PRICES, PRICE_ENTITY, set_prices

CONTROL = "sensor.ev_guest_charger_control"
CHARGE_NOW = "binary_sensor.ev_guest_charge_now"
STATUS = "sensor.ev_guest_status"
CAR = "binary_sensor.charger_car_connected"
METER = "sensor.charger_energy"

# The continuous example plans 22:00 → 02:40 (20 % → 80 % of 77 kWh at 11 kW).
START = timedelta(hours=2)
END = timedelta(hours=6, minutes=40)


async def _press(hass: HomeAssistant, key: str) -> None:
    await hass.services.async_call("button", "press", {ATTR_ENTITY_ID: f"button.ev_guest_{key}"}, blocking=True)
    await hass.async_block_till_done()


async def _move(hass: HomeAssistant, freezer: FrozenDateTimeFactory, moment: datetime) -> None:
    freezer.move_to(moment)
    async_fire_time_changed(hass, moment)
    await hass.async_block_till_done()


def _control(hass: HomeAssistant) -> str:
    state = hass.states.get(CONTROL)
    assert state is not None
    return state.state


def _attr(hass: HomeAssistant, name: str) -> object:
    state = hass.states.get(CONTROL)
    assert state is not None
    return state.attributes.get(name)


async def _car(hass: HomeAssistant, connected: bool) -> None:
    hass.states.async_set(CAR, "on" if connected else "off", {"device_class": "plug"})
    await hass.async_block_till_done()


@pytest.fixture
async def car_integration(hass: HomeAssistant, now: datetime, mock_config_entry: MockConfigEntry) -> MockConfigEntry:
    """EV Guest with a car connected sensor (and an energy meter)."""
    hass.states.async_set(CAR, "off", {"device_class": "plug"})
    hass.states.async_set(METER, "1000.0", {"unit_of_measurement": "kWh", "device_class": "energy"})
    set_prices(hass, now, CONTINUOUS_PRICES)
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, CONF_VEHICLE_ENTITY: CAR, CONF_ENERGY_ENTITY: METER},
    )
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry


async def test_released_without_a_plan(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    assert _control(hass) == "released"
    assert _attr(hass, "released_at") is None
    assert _attr(hass, "release_reason") is None
    assert _attr(hass, "car_connected") is None
    assert init_integration.runtime_data.release_info() is None


async def test_session_follows_the_plan_and_ends_with_it(
    hass: HomeAssistant, init_integration: MockConfigEntry, now: datetime, freezer: FrozenDateTimeFactory
) -> None:
    await _press(hass, "calculate")
    assert _control(hass) == "pause"
    assert _attr(hass, "session_ends") == (now + END).isoformat()
    assert _attr(hass, "released_at") is None

    await _move(hass, freezer, now + START)
    assert _control(hass) == "charge"
    assert hass.states.get(CHARGE_NOW).state == "on"

    # Without a car connected sensor the session ends exactly with the plan.
    await _move(hass, freezer, now + END)
    assert _control(hass) == "released"
    assert _attr(hass, "release_reason") == "plan_end"
    assert _attr(hass, "session_ends") is None
    assert hass.states.get(CHARGE_NOW).state == "off"
    assert hass.states.get(STATUS).state == "completed"

    # It stays released: nothing holds the charger for the owner's own car.
    await _move(hass, freezer, now + timedelta(days=2))
    assert _control(hass) == "released"

    state = panel_state(hass, init_integration.runtime_data)
    assert state["control"] == "released"
    assert state["release"]["reason"] == "plan_end"
    diagnostics = await async_get_config_entry_diagnostics(hass, init_integration)
    assert diagnostics["charger_control"] == "released"


async def test_new_guest_releases_the_charger(
    hass: HomeAssistant, init_integration: MockConfigEntry, now: datetime, freezer: FrozenDateTimeFactory
) -> None:
    await _press(hass, "calculate")
    await _move(hass, freezer, now + START + timedelta(hours=1))
    assert _control(hass) == "charge"

    await _press(hass, "new_guest")
    assert _control(hass) == "released"
    assert _attr(hass, "release_reason") == "new_guest"

    # A new plan starts a new session.
    await _press(hass, "calculate")
    assert _control(hass) in ("charge", "pause")
    assert _attr(hass, "released_at") is None


async def test_failed_calculation_releases_the_charger(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    await _press(hass, "calculate")
    assert _control(hass) == "pause"

    hass.states.async_set(PRICE_ENTITY, "0", {})
    with pytest.raises(ServiceValidationError):
        await _press(hass, "calculate")
    assert _control(hass) == "released"
    assert _attr(hass, "release_reason") == "cleared"


async def test_unplugging_ends_the_session(
    hass: HomeAssistant, car_integration: MockConfigEntry, now: datetime, freezer: FrozenDateTimeFactory
) -> None:
    await _car(hass, True)
    assert _attr(hass, "car_connected") is True
    await _press(hass, "calculate")
    await _move(hass, freezer, now + START + timedelta(hours=1))  # 23:00, charging
    assert _control(hass) == "charge"
    hass.states.async_set(METER, "1010.0", {"unit_of_measurement": "kWh"})
    await hass.async_block_till_done()

    # A short glitch of the sensor does not end the session.
    await _car(hass, False)
    await _move(hass, freezer, now + START + timedelta(hours=1, seconds=30))
    await _car(hass, True)
    await _move(hass, freezer, now + START + timedelta(hours=1, minutes=5))
    assert _control(hass) == "charge"

    # Unplugged for a minute: the guest has left.
    await _car(hass, False)
    assert _control(hass) == "charge"
    unplugged = now + START + timedelta(hours=1, minutes=7)
    await _move(hass, freezer, unplugged)
    assert _control(hass) == "released"
    assert _attr(hass, "release_reason") == "unplugged"
    assert hass.states.get(CHARGE_NOW).state == "off"
    assert hass.states.get(STATUS).state == "completed"

    # The finished part is in the history, and another car is not billed to the guest.
    coordinator = car_integration.runtime_data
    [entry] = coordinator.history
    assert entry["measured_energy"] == pytest.approx(10)
    assert datetime.fromisoformat(entry["end"]) <= unplugged
    hass.states.async_set(METER, "1030.0", {"unit_of_measurement": "kWh"})
    await hass.async_block_till_done()
    assert float(hass.states.get("sensor.ev_guest_measured_energy").state) == pytest.approx(10)

    # The estimate stops where the guest left.
    estimate = float(hass.states.get("sensor.ev_guest_estimated_soc").state)
    await _move(hass, freezer, now + START + timedelta(hours=3))
    assert float(hass.states.get("sensor.ev_guest_estimated_soc").state) == estimate

    # Plugging in again (the owner's car) is not a guest.
    await _car(hass, True)
    assert _control(hass) == "released"

    # Survives a reload.
    assert await hass.config_entries.async_reload(car_integration.entry_id)
    await hass.async_block_till_done()
    assert _control(hass) == "released"
    assert _attr(hass, "release_reason") == "unplugged"


async def test_unplugged_before_the_plan_starts(
    hass: HomeAssistant, car_integration: MockConfigEntry, now: datetime, freezer: FrozenDateTimeFactory
) -> None:
    await _car(hass, True)
    await _press(hass, "calculate")
    await _car(hass, False)
    await _move(hass, freezer, now + timedelta(minutes=2))
    assert _control(hass) == "released"
    # Nothing was charged, so nothing goes in the history.
    assert car_integration.runtime_data.history == []
    # Price updates no longer plan for the guest who left.
    set_prices(hass, now, [price + 0.01 for price in CONTINUOUS_PRICES])
    await hass.async_block_till_done()
    assert _control(hass) == "released"


async def test_guest_car_still_plugged_in_after_the_plan_is_held(
    hass: HomeAssistant, car_integration: MockConfigEntry, now: datetime, freezer: FrozenDateTimeFactory
) -> None:
    await _car(hass, True)
    await _press(hass, "calculate")

    # After the plan the guest car stays paused, so it does not charge on.
    await _move(hass, freezer, now + END + timedelta(minutes=30))
    assert _control(hass) == "pause"
    assert hass.states.get(STATUS).state == "completed"

    # Unplugging after the plan releases the charger right away.
    await _car(hass, False)
    assert _control(hass) == "released"
    assert _attr(hass, "release_reason") == "unplugged"


async def test_hold_after_the_plan_is_limited(
    hass: HomeAssistant, car_integration: MockConfigEntry, now: datetime, freezer: FrozenDateTimeFactory
) -> None:
    await _car(hass, True)
    await _press(hass, "calculate")
    await _move(hass, freezer, now + END + timedelta(hours=23))
    assert _control(hass) == "pause"

    # Never longer than 24 hours, even if the sensor still says connected.
    await _move(hass, freezer, now + END + timedelta(hours=24))
    assert _control(hass) == "released"
    assert _attr(hass, "release_reason") == "plan_end"


async def test_plan_end_while_unplugged_releases(
    hass: HomeAssistant, car_integration: MockConfigEntry, now: datetime, freezer: FrozenDateTimeFactory
) -> None:
    await _press(hass, "calculate")  # no car plugged in yet
    await _move(hass, freezer, now + END)
    assert _control(hass) == "released"
    assert _attr(hass, "release_reason") == "plan_end"


async def test_options_flow_sets_car_connected_sensor(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    hass.states.async_set(CAR, "on", {"device_class": "plug"})
    result = await hass.config_entries.options.async_init(init_integration.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_CURRENCY: "DKK", CONF_VEHICLE_ENTITY: CAR}
    )
    await hass.async_block_till_done()

    assert init_integration.options == {CONF_CURRENCY: "DKK", CONF_VEHICLE_ENTITY: CAR}
    assert _attr(hass, "car_connected") is True
