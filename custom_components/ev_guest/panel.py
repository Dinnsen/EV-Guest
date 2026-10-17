"""Sidebar panel and home-screen app for EV Guest."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant, callback
from homeassistant.loader import async_get_integration

from .const import DOMAIN

PANEL_URL = "ev-guest"
STATIC_URL = "/ev_guest_static"
APP_URL = "/ev_guest_app"
WEBCOMPONENT = "ev-guest-panel"
_STATIC_KEY = f"{DOMAIN}_static_registered"


async def async_register_panel(hass: HomeAssistant) -> None:
    """Serve the panel files and add the panel to the sidebar."""
    if not hass.data.get(_STATIC_KEY):
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(STATIC_URL, str(Path(__file__).parent / "frontend"), True),
                # Home-screen web app; not cached, so the launcher can change.
                StaticPathConfig(APP_URL, str(Path(__file__).parent / "app"), False),
            ]
        )
        hass.data[_STATIC_KEY] = True

    if PANEL_URL in hass.data.get(frontend.DATA_PANELS, {}):
        return
    version = (await async_get_integration(hass, DOMAIN)).version
    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL_URL,
        webcomponent_name=WEBCOMPONENT,
        sidebar_title="EV Guest",
        sidebar_icon="mdi:ev-station",
        module_url=f"{STATIC_URL}/{WEBCOMPONENT}.js?v={version}",
        config={"static_url": STATIC_URL, "app_url": APP_URL, "version": str(version)},
        require_admin=False,
    )


@callback
def async_unregister_panel(hass: HomeAssistant) -> None:
    """Remove the panel when the last EV Guest is unloaded."""
    if PANEL_URL in hass.data.get(frontend.DATA_PANELS, {}):
        frontend.async_remove_panel(hass, PANEL_URL)
