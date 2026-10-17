"""Tests for the sidebar panel registration."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.components import frontend
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ev_guest import panel


async def test_register_and_remove_panel(hass: HomeAssistant) -> None:
    """Files are served once, the panel is added once and removed again."""
    hass.http = MagicMock()
    hass.http.async_register_static_paths = AsyncMock()

    async def fake_register(hass: HomeAssistant, **kwargs: object) -> None:
        hass.data.setdefault(frontend.DATA_PANELS, {})[kwargs["frontend_url_path"]] = kwargs

    with (
        patch.object(panel.panel_custom, "async_register_panel", side_effect=fake_register) as add,
        patch.object(panel.frontend, "async_remove_panel") as remove,
    ):
        await panel.async_register_panel(hass)
        await panel.async_register_panel(hass)  # second EV Guest: nothing new

        hass.http.async_register_static_paths.assert_awaited_once()
        paths = hass.http.async_register_static_paths.call_args.args[0]
        assert [(path.url_path, path.cache_headers) for path in paths] == [
            ("/ev_guest_static", True),
            ("/ev_guest_app", False),
        ]
        add.assert_called_once()
        kwargs = add.call_args.kwargs
        assert kwargs["frontend_url_path"] == "ev-guest"
        assert kwargs["webcomponent_name"] == "ev-guest-panel"
        version = kwargs["config"]["version"]
        assert kwargs["module_url"] == f"/ev_guest_static/ev-guest-panel.js?v={version}"
        assert kwargs["require_admin"] is False

        panel.async_unregister_panel(hass)
        remove.assert_called_once_with(hass, "ev-guest")

        hass.data[frontend.DATA_PANELS].clear()
        panel.async_unregister_panel(hass)  # already gone
        remove.assert_called_once()


async def test_panel_follows_entries(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_panel: tuple[AsyncMock, MagicMock]
) -> None:
    register, unregister = mock_panel
    register.assert_awaited_once()

    await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()

    unregister.assert_called_once()
