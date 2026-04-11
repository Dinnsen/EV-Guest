"""Tests for EV Guest diagnostics redaction."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.ev_guest.diagnostics import async_get_config_entry_diagnostics


@pytest.mark.asyncio
async def test_diagnostics_redacts_sensitive_values(mock_hass) -> None:
    entry = SimpleNamespace(
        data={
            "motorapi_api_key": "super-secret",
            "price_entity": "sensor.energi_data_service",
        },
        options={},
        runtime_data=SimpleNamespace(
            data=SimpleNamespace(
                inputs={"license_plate": "EN17765", "soc": 42},
                results={"vin": "W1N1234567890", "car_model": "EQB"},
                service_health={"motorapi": True},
            )
        ),
    )

    diagnostics = await async_get_config_entry_diagnostics(mock_hass, entry)

    assert diagnostics["entry"]["motorapi_api_key"] == "**REDACTED**"
    assert diagnostics["inputs"]["license_plate"] == "**REDACTED**"
    assert diagnostics["results"]["vin"] == "**REDACTED**"
    assert diagnostics["service_health"] == {"motorapi": True}
