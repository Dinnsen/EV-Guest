from custom_components.ev_guest import async_migrate_entry


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
    assert kwargs["data"]["charger_switch_entity"] == ""
    assert kwargs["data"]["charger_status_entity"] == "binary_sensor.test_charger_status"
    assert "language" not in kwargs["data"]
    assert kwargs["data"]["country"] == "Denmark"
