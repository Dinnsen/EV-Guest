from __future__ import annotations

import pytest

from custom_components.ev_guest import async_migrate_entry


@pytest.mark.asyncio
async def test_migrate_old_entry(mock_hass, mock_config_entry):
    mock_config_entry.version = 6
    mock_config_entry.data["country"] = "dk"
    mock_config_entry.data["language"] = "English"
    mock_config_entry.data["charger_switch_entity"] = "switch.ev_guest_dummy_test_charger"

    ok = await async_migrate_entry(mock_hass, mock_config_entry)

    assert ok is True
    mock_hass.config_entries.async_update_entry.assert_called_once()
    _entry, kwargs = mock_hass.config_entries.async_update_entry.call_args
    assert kwargs["version"] == 7
    # Legacy charger keys are left untouched so a rollback to 0.6.x keeps working.
    assert kwargs["data"]["charger_switch_entity"] == "switch.ev_guest_dummy_test_charger"
    assert "language" not in kwargs["data"]
    assert kwargs["data"]["country"] == "Denmark"
