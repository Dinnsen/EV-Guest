from custom_components.ev_guest import async_migrate_entry


async def test_migrate_old_entry(hass, mock_config_entry):
    mock_config_entry.version = 3
    ok = await async_migrate_entry(hass, mock_config_entry)
    assert ok is True
    assert mock_config_entry.version == 4
    assert mock_config_entry.minor_version == 0
