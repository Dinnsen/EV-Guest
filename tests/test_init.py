"""Tests for setup, unload, migration, actions, repairs and diagnostics."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er, issue_registry as ir
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ev_guest.api import EVGuestAuthError, EVGuestLookupError
from custom_components.ev_guest.const import DOMAIN
from custom_components.ev_guest.diagnostics import async_get_config_entry_diagnostics

from .conftest import CONTINUOUS_PRICES, PRICE_ENTITY, set_prices

VALIDATE = "custom_components.ev_guest.coordinator.async_validate_plate_provider_credentials"


async def test_setup_and_unload(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    assert init_integration.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()

    assert init_integration.state is ConfigEntryState.NOT_LOADED


async def test_remove_entry_deletes_storage(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_storage: dict
) -> None:
    hass_storage[f"{DOMAIN}.{init_integration.entry_id}"] = {"version": 1, "key": "x", "data": {}}

    await hass.config_entries.async_remove(init_integration.entry_id)
    await hass.async_block_till_done()

    assert f"{DOMAIN}.{init_integration.entry_id}" not in hass_storage


@pytest.mark.parametrize(
    ("side_effect", "state"),
    [
        (EVGuestAuthError("invalid_auth"), ConfigEntryState.SETUP_ERROR),
        (EVGuestLookupError("unsupported_provider"), ConfigEntryState.SETUP_ERROR),
        (EVGuestLookupError("timeout"), ConfigEntryState.LOADED),
        (None, ConfigEntryState.LOADED),
    ],
)
async def test_setup_validates_key(
    hass: HomeAssistant,
    now: datetime,
    mock_config_entry: MockConfigEntry,
    side_effect: Exception | None,
    state: ConfigEntryState,
) -> None:
    set_prices(hass, now, CONTINUOUS_PRICES)
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(mock_config_entry, data={**mock_config_entry.data, "motorapi_api_key": "k"})

    with patch(VALIDATE, side_effect=side_effect):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state is state
    if state is ConfigEntryState.LOADED:
        await hass.config_entries.async_unload(mock_config_entry.entry_id)


async def test_legacy_entities_are_removed(
    hass: HomeAssistant, now: datetime, mock_config_entry: MockConfigEntry
) -> None:
    set_prices(hass, now, CONTINUOUS_PRICES)
    mock_config_entry.add_to_hass(hass)
    registry = er.async_get(hass)
    switch = registry.async_get_or_create(
        "switch", DOMAIN, f"{mock_config_entry.entry_id}_enable_charger_control", config_entry=mock_config_entry
    )
    text = registry.async_get_or_create(
        "text", DOMAIN, f"{mock_config_entry.entry_id}_charge_completion_time", config_entry=mock_config_entry
    )

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert registry.async_get(switch.entity_id) is None
    assert registry.async_get(text.entity_id) is None
    assert hass.states.get("time.ev_guest_charge_completion_time") is not None
    await hass.config_entries.async_unload(mock_config_entry.entry_id)


async def test_migrate_7_0_moves_connection_options_to_data(hass: HomeAssistant, now: datetime) -> None:
    set_prices(hass, now, CONTINUOUS_PRICES)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="EV Guest",
        unique_id="EV Guest",
        data={
            "name": "EV Guest",
            "price_entity": "sensor.old",
            "currency": "DKK",
            "time_format": "24h",
            "motorapi_api_key": "",
            "country": "Denmark",
            "charger_switch_entity": "switch.x",
        },
        options={"price_entity": PRICE_ENTITY, "motorapi_api_key": "", "currency": "EUR"},
        version=7,
        minor_version=0,
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.minor_version == 1
    assert entry.data["price_entity"] == PRICE_ENTITY
    assert entry.data["charger_switch_entity"] == "switch.x"  # kept for rollback
    assert entry.options == {"currency": "EUR"}
    await hass.config_entries.async_unload(entry.entry_id)


async def test_migrate_from_version_6(hass: HomeAssistant, now: datetime) -> None:
    set_prices(hass, now, CONTINUOUS_PRICES)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="EV Guest",
        data={"country": "dk", "language": "English"},
        options={"country": "DK", "language": "Dansk"},
        version=6,
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert (entry.version, entry.minor_version) == (7, 1)
    assert entry.data["country"] == "Denmark"
    assert entry.data["price_entity"] == PRICE_ENTITY
    assert "language" not in entry.data
    assert entry.options == {}
    await hass.config_entries.async_unload(entry.entry_id)


async def test_future_version_is_not_migrated(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(domain=DOMAIN, title="EV Guest", data={}, version=8)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)

    assert entry.state is ConfigEntryState.MIGRATION_ERROR


async def test_actions(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    await hass.services.async_call(DOMAIN, "calculate", {}, blocking=True)
    assert hass.states.get("sensor.ev_guest_status").state == "planned"

    await hass.services.async_call(DOMAIN, "calculate", {"config_entry_id": init_integration.entry_id}, blocking=True)
    # The pre-0.8 field name still works.
    await hass.services.async_call(DOMAIN, "calculate", {"entry_id": init_integration.entry_id}, blocking=True)

    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call(DOMAIN, "grab_car_data", {}, blocking=True)
    assert err.value.translation_key == "license_plate_required"

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "calculate", {"config_entry_id": "unknown"}, blocking=True)


async def test_repair_issue_for_missing_price_sensor(
    hass: HomeAssistant, now: datetime, mock_config_entry: MockConfigEntry
) -> None:
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    issue_id = f"price_entity_missing_{mock_config_entry.entry_id}"
    issue_registry = ir.async_get(hass)
    assert issue_registry.async_get_issue(DOMAIN, issue_id) is not None

    set_prices(hass, now, CONTINUOUS_PRICES)
    await hass.async_block_till_done()

    assert issue_registry.async_get_issue(DOMAIN, issue_id) is None
    await hass.config_entries.async_unload(mock_config_entry.entry_id)


async def test_diagnostics_redacts_secrets(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    hass.config_entries.async_update_entry(
        init_integration, data={**init_integration.data, "motorapi_api_key": "secret"}
    )
    init_integration.runtime_data.data.inputs["license_plate"] = "AB12345"

    diagnostics = await async_get_config_entry_diagnostics(hass, init_integration)

    assert diagnostics["entry"]["motorapi_api_key"] == "**REDACTED**"
    assert diagnostics["inputs"]["license_plate"] == "**REDACTED**"
    assert diagnostics["status"] == "ready"
    assert diagnostics["plan_locked"] is False
