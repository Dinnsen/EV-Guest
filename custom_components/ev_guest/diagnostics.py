"""Diagnostics support for EV Guest."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import REDACT_KEYS


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return {
        "entry": async_redact_data(dict(entry.data), REDACT_KEYS),
        "options": async_redact_data(dict(entry.options), REDACT_KEYS),
        "inputs": async_redact_data(dict(coordinator.data.inputs), REDACT_KEYS),
        "results": async_redact_data(dict(coordinator.data.results), REDACT_KEYS),
        "service_health": dict(coordinator.data.service_health),
        "plan_segments": coordinator.debug_plan_segments,
    }
