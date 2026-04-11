from datetime import datetime
from zoneinfo import ZoneInfo

from custom_components.ev_guest.coordinator import EVGuestCoordinator


def test_extract_price_slots_handles_none_lists(hass, mock_config_entry):
    coordinator = EVGuestCoordinator(hass, mock_config_entry)
    hass.states.async_set(
        "sensor.test_price",
        "1.0",
        {
            "raw_today": [{"hour": "2026-04-10T00:00:00+02:00", "price": 1.0}],
            "raw_tomorrow": None,
            "forecast": None,
        },
    )

    slots = coordinator._extract_price_slots()

    assert len(slots) == 1
    assert slots[0][1] == 1.0
