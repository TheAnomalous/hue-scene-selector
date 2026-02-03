"""Config flow for Hue Scene Selector integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def get_hue_bridges(hass: HomeAssistant) -> dict[str, str]:
    """Get all configured Hue bridges."""
    bridges = {}
    
    # Find all Hue config entries
    for entry in hass.config_entries.async_entries("hue"):
        if entry.unique_id:
            bridges[entry.entry_id] = entry.title or f"Hue Bridge ({entry.unique_id[:8]})"
    
    return bridges


class HueSceneSelectorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hue Scene Selector."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        # Get available Hue bridges
        bridges = get_hue_bridges(self.hass)
        
        if not bridges:
            return self.async_abort(reason="no_hue_bridges")
        
        if user_input is not None:
            bridge_id = user_input["bridge"]
            bridge_name = bridges.get(bridge_id, "Hue Bridge")
            
            # Check if already configured for this bridge
            await self.async_set_unique_id(f"hue_scene_selector_{bridge_id}")
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(
                title=f"Scene Selectors - {bridge_name}",
                data={"bridge_id": bridge_id},
            )
        
        # Show selection form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("bridge"): vol.In(bridges),
            }),
            errors=errors,
            description_placeholders={
                "bridge_count": str(len(bridges)),
            },
        )
