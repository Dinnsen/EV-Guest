"""Tests for planning, plan state and entities with a real Home Assistant."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from unittest.mock import patch

from freezegun.api import FrozenDateTimeFactory
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed

from custom_components.ev_guest.api import (
    BatteryLookupResult,
    EVGuestAuthError,
    EVGuestLookupError,
    VehicleLookupResult,
)
from custom_components.ev_guest.const import CONF_MOTORAPI_KEY, DOMAIN, STORAGE_KEY

from .conftest import CONTINUOUS_PRICES, SPLIT_PRICES, set_prices

STATUS = "sensor.ev_guest_status"
CHARGE_NOW = "binary_sensor.ev_guest_charge_now"
START = "sensor.ev_guest_charge_start_time"
END = "sensor.ev_guest_charge_end_time"
CHARGE_TIME = "sensor.ev_guest_charge_time"
COSTS = "sensor.ev_guest_charge_costs"
SPEED = "sensor.ev_guest_charging_speed"
CALCULATE = "button.ev_guest_calculate"
GRAB = "button.ev_guest_grab_car_data"
SOC = "number.ev_guest_soc_state_of_charge"
LIMIT = "number.ev_guest_charge_limit"
COMPLETION = "time.ev_guest_charge_completion_time"
PLATE = "text.ev_guest_license_plate"
CONTINUOUS = "switch.ev_guest_continuous_charging_preferred"
USE_COMPLETION = "switch.ev_guest_use_charge_completion_time"


async def _press(hass: HomeAssistant, entity_id: str) -> None:
    await hass.services.async_call("button", "press", {ATTR_ENTITY_ID: entity_id}, blocking=True)
    await hass.async_block_till_done()


async def _set_number(hass: HomeAssistant, entity_id: str, value: float) -> None:
    await hass.services.async_call("number", "set_value", {ATTR_ENTITY_ID: entity_id, "value": value}, blocking=True)


async def _move(hass: HomeAssistant, freezer: FrozenDateTimeFactory, moment: datetime) -> None:
    freezer.move_to(moment)
    async_fire_time_changed(hass, moment)
    await hass.async_block_till_done()


def _state(hass: HomeAssistant, entity_id: str) -> Any:
    state = hass.states.get(entity_id)
    assert state is not None, entity_id
    return state


async def test_entities_and_defaults(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """All entities exist with sensible initial states."""
    assert _state(hass, STATUS).state == "ready"
    assert _state(hass, CHARGE_NOW).state == STATE_OFF
    assert _state(hass, START).state == STATE_UNKNOWN
    assert _state(hass, SOC).state == "20.0"
    assert _state(hass, COMPLETION).state == "07:00:00"
    assert _state(hass, CONTINUOUS).state == STATE_ON
    assert _state(hass, COSTS).attributes["unit_of_measurement"] == "DKK"
    assert _state(hass, STATUS).attributes["options"][:4] == ["ready", "planned", "charging", "completed"]


async def test_continuous_plan_runs_through_its_states(
    hass: HomeAssistant, init_integration: MockConfigEntry, now: datetime, freezer: FrozenDateTimeFactory
) -> None:
    """Calculate, then follow the plan from planned to charging to completed."""
    await _press(hass, CALCULATE)

    assert _state(hass, STATUS).state == "planned"
    assert _state(hass, START).state == "2026-04-09T20:00:00+00:00"
    assert _state(hass, END).state == "2026-04-10T00:12:00+00:00"
    assert _state(hass, CHARGE_TIME).state == "252"
    assert float(_state(hass, COSTS).state) == pytest.approx(14.63, rel=1e-3)
    assert float(_state(hass, SPEED).state) == pytest.approx(14.3)
    attrs = _state(hass, STATUS).attributes
    assert attrs["plan_mode"] == "continuous"
    assert attrs["plan_locked"] is False
    assert len(attrs["raw_two_days"]) == len(CONTINUOUS_PRICES)
    assert sum(row["value"] for row in attrs["charging_schedule"]) == 5

    await _move(hass, freezer, now + timedelta(hours=2, minutes=30))
    assert _state(hass, STATUS).state == "charging"
    assert _state(hass, CHARGE_NOW).state == STATE_ON
    assert _state(hass, STATUS).attributes["plan_locked"] is True

    await _move(hass, freezer, now + timedelta(hours=6, minutes=12))
    assert _state(hass, CHARGE_NOW).state == STATE_OFF
    assert _state(hass, STATUS).state == "completed"


async def test_split_plan(hass: HomeAssistant, init_integration: MockConfigEntry, now: datetime) -> None:
    set_prices(hass, now, SPLIT_PRICES)
    await hass.services.async_call("switch", "turn_off", {ATTR_ENTITY_ID: CONTINUOUS}, blocking=True)

    await _press(hass, CALCULATE)

    attrs = _state(hass, STATUS).attributes
    assert attrs["plan_mode"] == "split"
    assert [seg["start"][11:16] for seg in attrs["charging_segments"]] == ["21:00", "23:00", "00:48"]
    assert float(_state(hass, COSTS).state) == pytest.approx(23.98, rel=1e-3)


async def test_started_plan_is_locked_against_price_updates(
    hass: HomeAssistant, init_integration: MockConfigEntry, now: datetime, freezer: FrozenDateTimeFactory
) -> None:
    """A static start SoC must never make a running plan slide or repeat."""
    await _press(hass, CALCULATE)
    first = _state(hass, STATUS).attributes["charging_segments"]

    await _move(hass, freezer, now + timedelta(hours=3))
    set_prices(hass, now + timedelta(hours=3), [0.01] * 10)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert _state(hass, STATUS).attributes["charging_segments"] == first

    # Calculate always makes a new plan.
    await _press(hass, CALCULATE)
    assert _state(hass, STATUS).attributes["charging_segments"] != first


async def test_plan_that_has_not_started_follows_new_prices(
    hass: HomeAssistant, init_integration: MockConfigEntry, now: datetime
) -> None:
    await _press(hass, CALCULATE)
    assert _state(hass, START).state == "2026-04-09T20:00:00+00:00"

    prices = list(CONTINUOUS_PRICES)
    prices[1] = 0.01
    set_prices(hass, now, prices)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert _state(hass, START).state == "2026-04-09T19:00:00+00:00"


async def test_price_updates_do_nothing_before_first_calculation(
    hass: HomeAssistant, init_integration: MockConfigEntry, now: datetime
) -> None:
    set_prices(hass, now, [0.01] * 11)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert _state(hass, STATUS).state == "ready"


async def test_waiting_for_prices_then_planning_automatically(
    hass: HomeAssistant, init_integration: MockConfigEntry, now: datetime
) -> None:
    """Pressing Calculate before enough prices exist plans once prices arrive."""
    set_prices(hass, now, [1.0, 1.0])

    with pytest.raises(ServiceValidationError) as err:
        await _press(hass, CALCULATE)
    assert err.value.translation_key == "not_enough_prices"
    assert _state(hass, STATUS).state == "not_enough_prices"

    set_prices(hass, now, CONTINUOUS_PRICES)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert _state(hass, STATUS).state == "planned"


@pytest.mark.parametrize(
    ("soc", "limit", "key"),
    [(80, 80, "limit_not_above_soc"), (20, 80, None)],
)
async def test_failed_calculation_clears_old_plan(
    hass: HomeAssistant, init_integration: MockConfigEntry, soc: float, limit: float, key: str | None
) -> None:
    await _press(hass, CALCULATE)
    await _set_number(hass, SOC, soc)
    await _set_number(hass, LIMIT, limit)

    if key is None:
        await _press(hass, CALCULATE)
        assert _state(hass, STATUS).state == "planned"
        return

    with pytest.raises(ServiceValidationError) as err:
        await _press(hass, CALCULATE)
    assert err.value.translation_key == key
    assert _state(hass, STATUS).state == key
    assert _state(hass, START).state == STATE_UNKNOWN


async def test_missing_price_data(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    hass.states.async_set("sensor.energi_data_service", "unavailable")

    with pytest.raises(ServiceValidationError):
        await _press(hass, CALCULATE)
    assert _state(hass, STATUS).state == "no_price_data"


async def test_invalid_input(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    init_integration.runtime_data.data.inputs["battery_capacity"] = 0

    with pytest.raises(ServiceValidationError):
        await _press(hass, CALCULATE)
    assert _state(hass, STATUS).state == "invalid_input"


async def test_without_completion_time_uses_two_day_horizon(
    hass: HomeAssistant, init_integration: MockConfigEntry, now: datetime
) -> None:
    set_prices(hass, now, [1.0] * 48 + [0.01])
    await hass.services.async_call("switch", "turn_off", {ATTR_ENTITY_ID: USE_COMPLETION}, blocking=True)

    await _press(hass, CALCULATE)

    assert _state(hass, START).state == "2026-04-09T18:00:00+00:00"
    assert len(_state(hass, STATUS).attributes["raw_two_days"]) == 48


async def test_inputs_are_saved_and_restored(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    hass_storage: dict[str, Any],
    freezer: FrozenDateTimeFactory,
    now: datetime,
) -> None:
    await _set_number(hass, SOC, 42)
    await hass.services.async_call("time", "set_value", {ATTR_ENTITY_ID: COMPLETION, "time": "06:30"}, blocking=True)
    await hass.services.async_call("text", "set_value", {ATTR_ENTITY_ID: PLATE, "value": " ab12345 "}, blocking=True)
    await _press(hass, CALCULATE)
    await _move(hass, freezer, now + timedelta(seconds=5))

    stored = hass_storage[STORAGE_KEY.format(entry_id=init_integration.entry_id)]["data"]
    assert stored["inputs"]["soc"] == 42
    assert stored["inputs"]["charge_completion_time"] == "06:30"
    assert stored["auto_recalculate"] is True

    await hass.config_entries.async_reload(init_integration.entry_id)
    await hass.async_block_till_done()

    assert _state(hass, SOC).state == "42.0"
    assert _state(hass, COMPLETION).state == "06:30:00"
    assert _state(hass, PLATE).state == "AB12345"
    assert _state(hass, STATUS).state == "planned"


async def test_restores_state_stored_by_0_7(
    hass: HomeAssistant, now: datetime, mock_config_entry: MockConfigEntry, hass_storage: dict[str, Any]
) -> None:
    """0.7.x stored text times and possibly a text charge time."""
    hass_storage[STORAGE_KEY.format(entry_id=mock_config_entry.entry_id)] = {
        "version": 1,
        "minor_version": 1,
        "key": STORAGE_KEY.format(entry_id=mock_config_entry.entry_id),
        "data": {
            "inputs": {"charge_completion_time": "6:15 AM", "soc": 30},
            "results": {"charge_time": "4h 12m", "charge_start_time": "22:00", "status": "Calculation ready"},
            "segments": [
                {"start": (now + timedelta(hours=1)).isoformat(), "end": (now + timedelta(hours=2)).isoformat()}
            ],
            "auto_recalculate": True,
        },
    }
    set_prices(hass, now, CONTINUOUS_PRICES)
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert _state(hass, COMPLETION).state == "06:15:00"
    assert _state(hass, CHARGE_TIME).state == STATE_UNKNOWN
    assert _state(hass, STATUS).state == "planned"
    assert _state(hass, START).state == "2026-04-09T19:00:00+00:00"
    await hass.config_entries.async_unload(mock_config_entry.entry_id)


async def test_switch_turn_on(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    await hass.services.async_call("switch", "turn_off", {ATTR_ENTITY_ID: USE_COMPLETION}, blocking=True)
    assert _state(hass, USE_COMPLETION).state == STATE_OFF
    await hass.services.async_call("switch", "turn_on", {ATTR_ENTITY_ID: USE_COMPLETION}, blocking=True)
    assert _state(hass, USE_COMPLETION).state == STATE_ON


async def test_entity_registry_unique_ids(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, init_integration.entry_id)
    assert {entry.unique_id.removeprefix(f"{init_integration.entry_id}_") for entry in entries} == {
        "charge_now",
        "grab_car_data",
        "calculate",
        "soc",
        "charge_limit",
        "battery_capacity",
        "charger_power",
        "charging_speed",
        "charge_start_time",
        "charge_end_time",
        "charge_time",
        "charge_costs",
        "status",
        "car_brand",
        "car_model",
        "car_variant",
        "car_battery_capacity",
        "use_completion_time",
        "continuous_charging_preferred",
        "license_plate",
        "charge_completion_time",
    }


# ----------------------------------------------------------------------
# Car lookup


async def test_lookup_requires_plate_and_key(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    with pytest.raises(ServiceValidationError) as err:
        await _press(hass, GRAB)
    assert err.value.translation_key == "license_plate_required"

    await hass.services.async_call("text", "set_value", {ATTR_ENTITY_ID: PLATE, "value": "AB12345"}, blocking=True)
    with pytest.raises(ServiceValidationError) as err:
        await _press(hass, GRAB)
    assert err.value.translation_key == "motorapi_key_missing"
    # Lookup errors never replace the plan status.
    assert _state(hass, STATUS).state == "ready"


@pytest.fixture
async def keyed_integration(hass: HomeAssistant, now: datetime, mock_config_entry: MockConfigEntry) -> MockConfigEntry:
    """EV Guest with a MotorAPI key and a plate entered."""
    set_prices(hass, now, CONTINUOUS_PRICES)
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(mock_config_entry, data={**mock_config_entry.data, CONF_MOTORAPI_KEY: "key"})
    with patch("custom_components.ev_guest.coordinator.async_validate_plate_provider_credentials"):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    await hass.services.async_call("text", "set_value", {ATTR_ENTITY_ID: PLATE, "value": "AB12345"}, blocking=True)
    return mock_config_entry


async def test_lookup_fills_car_data(hass: HomeAssistant, keyed_integration: MockConfigEntry) -> None:
    vehicle = VehicleLookupResult("AB12345", "VIN123", "Tesla", "Model 3", None, 2023, "El", "MotorAPI", {})
    decoded = VehicleLookupResult("", "VIN123", "Tesla", "Model 3", "Long Range", 2023, None, "NHTSA vPIC", {})
    battery = BatteryLookupResult(75.0, "Open EV Data", 90.0, {"x": 1})
    with (
        patch("custom_components.ev_guest.coordinator.async_lookup_vehicle", return_value=vehicle),
        patch("custom_components.ev_guest.coordinator.async_decode_vin_nhtsa", return_value=decoded),
        patch("custom_components.ev_guest.coordinator.async_lookup_battery_open_ev_data", return_value=battery),
    ):
        await _press(hass, GRAB)

    assert _state(hass, "sensor.ev_guest_car_brand").state == "Tesla"
    assert _state(hass, "sensor.ev_guest_car_variant").state == "Long Range"
    assert _state(hass, "sensor.ev_guest_car_battery_capacity").state == "75.0"
    assert _state(hass, "number.ev_guest_battery_capacity").state == "75.0"
    assert _state(hass, STATUS).attributes["vin"] == "VIN123"
    await hass.config_entries.async_unload(keyed_integration.entry_id)


@pytest.mark.parametrize(
    ("error", "exception", "key"),
    [
        (EVGuestAuthError("invalid_auth"), ServiceValidationError, "invalid_api_key"),
        (EVGuestLookupError("vehicle_not_found"), ServiceValidationError, "vehicle_not_found"),
        (EVGuestLookupError("timeout"), HomeAssistantError, "lookup_failed"),
    ],
)
async def test_lookup_errors(
    hass: HomeAssistant, keyed_integration: MockConfigEntry, error: Exception, exception: type[Exception], key: str
) -> None:
    with (
        patch("custom_components.ev_guest.coordinator.async_lookup_vehicle", side_effect=error),
        pytest.raises(exception) as err,
    ):
        await _press(hass, GRAB)
    assert err.value.translation_key == key
    if key == "invalid_api_key":
        flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
        assert flows and flows[0]["context"]["source"] == "reauth"
    await hass.config_entries.async_unload(keyed_integration.entry_id)


async def test_lookup_without_vin_or_battery_match(hass: HomeAssistant, keyed_integration: MockConfigEntry) -> None:
    vehicle = VehicleLookupResult("AB12345", None, "Fiat", "500e", None, None, None, "MotorAPI", {})
    with (
        patch("custom_components.ev_guest.coordinator.async_lookup_vehicle", return_value=vehicle),
        patch(
            "custom_components.ev_guest.coordinator.async_lookup_battery_open_ev_data",
            return_value=BatteryLookupResult(None, "Open EV Data", 10.0, None),
        ),
    ):
        await _press(hass, GRAB)

    assert _state(hass, "sensor.ev_guest_car_brand").state == "Fiat"
    assert _state(hass, "number.ev_guest_battery_capacity").state == "77.0"
    await hass.config_entries.async_unload(keyed_integration.entry_id)


async def test_no_window_before_completion_time(
    hass: HomeAssistant, init_integration: MockConfigEntry, now: datetime
) -> None:
    """Enough prices before the deadline, but no block ends in time."""
    set_prices(hass, now, [1.0, 1.0, 1.0, 1.0])
    await _set_number(hass, SOC, 0)
    await _set_number(hass, LIMIT, 100)
    await _set_number(hass, "number.ev_guest_battery_capacity", 30)
    await _set_number(hass, "number.ev_guest_charger_power", 10)
    await hass.services.async_call("time", "set_value", {ATTR_ENTITY_ID: COMPLETION, "time": "22:30"}, blocking=True)

    with pytest.raises(ServiceValidationError) as err:
        await _press(hass, CALCULATE)
    assert err.value.translation_key == "no_window"


async def test_non_numeric_input(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    init_integration.runtime_data.data.inputs["soc"] = None

    with pytest.raises(ServiceValidationError) as err:
        await _press(hass, CALCULATE)
    assert err.value.translation_key == "invalid_input"


async def test_automatic_recalculation_failure(
    hass: HomeAssistant, init_integration: MockConfigEntry, now: datetime
) -> None:
    """A failing automatic recalculation keeps a pending plan, or shows why there is none."""
    coordinator = init_integration.runtime_data
    await _press(hass, CALCULATE)
    plan = _state(hass, STATUS).attributes["charging_segments"]

    hass.states.async_set("sensor.energi_data_service", "unavailable")
    await hass.async_block_till_done(wait_background_tasks=True)
    assert _state(hass, STATUS).state == "planned"
    assert _state(hass, STATUS).attributes["charging_segments"] == plan

    coordinator._set_plan([])
    await coordinator.async_calculate(manual=False)
    await hass.async_block_till_done()
    assert _state(hass, STATUS).state == "no_price_data"


async def test_automatic_recalculation_skipped_when_locked(
    hass: HomeAssistant, init_integration: MockConfigEntry, now: datetime, freezer: FrozenDateTimeFactory
) -> None:
    coordinator = init_integration.runtime_data
    await _press(hass, CALCULATE)
    await _move(hass, freezer, now + timedelta(hours=3))
    plan = list(coordinator._plan_segments)

    await coordinator.async_calculate(manual=False)

    assert coordinator._plan_segments == plan


async def test_service_health_recovers(hass: HomeAssistant, keyed_integration: MockConfigEntry) -> None:
    vehicle = VehicleLookupResult("AB12345", None, "Fiat", "500e", None, None, None, "MotorAPI", {})
    with (
        patch("custom_components.ev_guest.coordinator.async_lookup_vehicle", side_effect=EVGuestLookupError("timeout")),
        pytest.raises(HomeAssistantError),
    ):
        await _press(hass, GRAB)
    assert _state(hass, "sensor.ev_guest_car_brand").state == "unavailable"

    with (
        patch("custom_components.ev_guest.coordinator.async_lookup_vehicle", return_value=vehicle),
        patch(
            "custom_components.ev_guest.coordinator.async_lookup_battery_open_ev_data",
            return_value=BatteryLookupResult(37.3, "Open EV Data", 80.0, {}),
        ),
    ):
        await _press(hass, GRAB)
    assert _state(hass, "sensor.ev_guest_car_brand").state == "Fiat"
    await hass.config_entries.async_unload(keyed_integration.entry_id)
