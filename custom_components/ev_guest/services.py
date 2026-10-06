"""Actions for EV Guest."""

from __future__ import annotations

from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv, service
import voluptuous as vol

from .const import ATTR_CONFIG_ENTRY_ID, DOMAIN, SERVICE_CALCULATE, SERVICE_GRAB_CAR_DATA
from .coordinator import EVGuestCoordinator

# "entry_id" is the field name used before 0.8.0 and is still accepted.
SERVICE_SCHEMA = vol.All(
    cv.has_at_most_one_key(ATTR_CONFIG_ENTRY_ID, "entry_id"),
    vol.Schema(
        {
            vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
            vol.Optional("entry_id"): cv.string,
        }
    ),
)


def _get_coordinator(call: ServiceCall) -> EVGuestCoordinator:
    """Return the coordinator for the call; optional with a single entry."""
    entry_id = call.data.get(ATTR_CONFIG_ENTRY_ID) or call.data.get("entry_id")
    entry = service.async_get_config_entry(call.hass, DOMAIN, entry_id)
    return entry.runtime_data


async def _async_grab_car_data(call: ServiceCall) -> None:
    await _get_coordinator(call).async_lookup_car_data()


async def _async_calculate(call: ServiceCall) -> None:
    await _get_coordinator(call).async_calculate()


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register the EV Guest actions."""
    hass.services.async_register(DOMAIN, SERVICE_GRAB_CAR_DATA, _async_grab_car_data, schema=SERVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_CALCULATE, _async_calculate, schema=SERVICE_SCHEMA)
