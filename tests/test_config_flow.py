from __future__ import annotations

from custom_components.ev_guest.config_flow import EVGuestOptionsFlow
from custom_components.ev_guest.const import CONF_CHARGER_STATUS_ENTITY, CONF_CHARGER_SWITCH_ENTITY, CONF_COUNTRY, CONF_LANGUAGE, CONF_MOTORAPI_KEY


class DummyEntry:
    def __init__(self) -> None:
        self.data = {
            "price_entity": "sensor.energi_data_service",
            "currency": "DKK",
            "time_format": "24h",
            "duration_format": "minutes",
            "motorapi_api_key": "existing_key",
            "charger_switch_entity": "switch.test_charger",
            "charger_status_entity": "binary_sensor.test_charger_status",
            "language": "English",
            "country": "Denmark",
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
    assert flow._config_entry.data[CONF_CHARGER_SWITCH_ENTITY] == "switch.test_charger"


def test_existing_optional_fields_are_available_on_entry() -> None:
    entry = DummyEntry()
    flow = EVGuestOptionsFlow(entry)
    assert flow._config_entry.data[CONF_CHARGER_STATUS_ENTITY] == "binary_sensor.test_charger_status"
    assert flow._config_entry.data[CONF_LANGUAGE] == "English"
    assert flow._config_entry.data[CONF_COUNTRY] == "Denmark"
