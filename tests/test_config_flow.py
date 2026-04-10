from __future__ import annotations

from custom_components.ev_guest.const import (
    CONF_CURRENCY,
    CONF_DURATION_FORMAT,
    CONF_MOTORAPI_KEY,
    CONF_PRICE_ENTITY,
    CONF_TIME_FORMAT,
)
from custom_components.ev_guest.config_flow import EVGuestOptionsFlow


class DummyEntry:
    def __init__(self) -> None:
        self.data = {
            CONF_PRICE_ENTITY: "sensor.energi_data_service",
            CONF_CURRENCY: "DKK",
            CONF_TIME_FORMAT: "24h",
            CONF_DURATION_FORMAT: "minutes",
            CONF_MOTORAPI_KEY: "existing_key",
        }
        self.options = {}


def test_options_flow_uses_private_config_entry_attr() -> None:
    entry = DummyEntry()
    flow = EVGuestOptionsFlow(entry)
    assert flow._config_entry is entry


def test_existing_api_key_is_available_on_entry() -> None:
    entry = DummyEntry()
    flow = EVGuestOptionsFlow(entry)
    assert flow._config_entry.data[CONF_MOTORAPI_KEY] == "existing_key"
