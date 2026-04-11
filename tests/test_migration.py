from custom_components.ev_guest import async_migrate_entry


async def test_migrate_old_entry(mock_hass, mock_config_entry):
    mock_config_entry.version = 4
    ok = await async_migrate_entry(mock_hass, mock_config_entry)
    assert ok is True
    mock_hass.config_entries.async_update_entry.assert_called_once()
    _entry, kwargs = mock_hass.config_entries.async_update_entry.call_args
    assert kwargs["version"] == 5
    assert kwargs["data"]["charger_switch_entity"] == "switch.test_charger"
