from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from custom_components.ev_guest.coordinator import EVGuestCoordinator


def test_extract_price_slots_handles_none_lists(mock_hass, mock_config_entry, monkeypatch):
    monkeypatch.setattr(
        "custom_components.ev_guest.coordinator.async_get_clientsession",
        lambda hass: MagicMock(),
    )

    coordinator = EVGuestCoordinator(mock_hass, mock_config_entry)
    mock_hass.states.get.return_value = SimpleNamespace(
        state="1.0",
        attributes={
            "raw_today": [{"hour": "2026-04-10T00:00:00+02:00", "price": 1.0}],
            "raw_tomorrow": None,
            "forecast": None,
        },
    )

    slots = coordinator._extract_price_slots()

    assert len(slots) == 1
    assert slots[0][1] == 1.0
