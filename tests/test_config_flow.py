from __future__ import annotations

from custom_components.ev_guest.config_flow import EVGuestOptionsFlow, _options_schema, _user_schema
from custom_components.ev_guest.const import CONF_COUNTRY, CONF_MOTORAPI_KEY


class DummyEntry:
    def __init__(self) -> None:
        self.data = {
            "price_entity": "sensor.energi_data_service",
            "currency": "DKK",
            "time_format": "24h",
            "duration_format": "minutes",
            "motorapi_api_key": "existing_key",
            "country": "Denmark",
        }
        self.options = {}


def test_options_flow_uses_private_config_entry_attr() -> None:
    entry = DummyEntry()
    flow = EVGuestOptionsFlow(entry)
    assert flow._config_entry is entry


def test_existing_fields_are_available_on_entry() -> None:
    entry = DummyEntry()
    flow = EVGuestOptionsFlow(entry)
    assert flow._config_entry.data[CONF_MOTORAPI_KEY] == "existing_key"
    assert flow._config_entry.data[CONF_COUNTRY] == "Denmark"


def test_schemas_have_no_charger_fields(hass) -> None:
    for schema in (_user_schema(hass, {}), _options_schema(hass, {})):
        keys = {str(key) for key in schema.schema}
        assert "charger_switch_entity" not in keys
        assert "charger_status_entity" not in keys
        assert CONF_MOTORAPI_KEY in keys
