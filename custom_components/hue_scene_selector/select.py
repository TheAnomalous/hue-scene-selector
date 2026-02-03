"""Select platform for Hue Scene Selector."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.const import STATE_UNKNOWN

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def get_hue_rooms_and_scenes(hass: HomeAssistant) -> dict[str, dict[str, str]]:
    """
    Discover all Hue rooms/zones and their scenes.
    
    Returns a dict like:
    {
        "Bedroom": {"Bedroom Bright": "Bright", "Bedroom Relax": "Relax", ...},
        "Family Room": {"Family Room TV Glow": "TV Glow", ...},
    }
    
    The keys are friendly names (for display), values are scene names (for activation).
    """
    rooms: dict[str, dict[str, str]] = {}
    
    # Get all scene entities
    for state in hass.states.async_all("scene"):
        entity_id = state.entity_id
        friendly_name = state.name or entity_id
        
        # Parse room name from entity_id
        # Hue scenes typically look like: scene.bedroom_bright, scene.family_room_relax
        # We extract the room portion
        if entity_id.startswith("scene."):
            scene_part = entity_id[6:]  # Remove "scene." prefix
            
            # Try to find the room by checking against known patterns
            # This handles: bedroom_bright -> Bedroom, family_room_relax -> Family Room
            parts = scene_part.split("_")
            
            # Try different combinations to find the room
            for i in range(1, len(parts)):
                potential_room = "_".join(parts[:i])
                remaining = "_".join(parts[i:])
                
                # Check if this looks like a valid room by seeing if there's a light group
                room_formatted = potential_room.replace("_", " ").title()
                light_entity = f"light.{potential_room}"
                
                if hass.states.get(light_entity):
                    if room_formatted not in rooms:
                        rooms[room_formatted] = {}
                    
                    # Map friendly name -> actual scene name for the Hue bridge
                    # The scene name is the "remaining" part, formatted nicely
                    scene_name = remaining.replace("_", " ").title()
                    rooms[room_formatted][friendly_name] = scene_name
                    break
    
    # Sort scenes alphabetically within each room
    for room in rooms:
        rooms[room] = dict(sorted(rooms[room].items()))
    
    return rooms


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Hue Scene Selector select entities."""
    
    # Discover rooms and scenes
    rooms_and_scenes = await hass.async_add_executor_job(
        get_hue_rooms_and_scenes, hass
    )
    
    if not rooms_and_scenes:
        _LOGGER.warning("No Hue rooms/scenes found. Make sure the Hue integration is set up.")
        return
    
    entities = []
    for room_name, scene_map in rooms_and_scenes.items():
        if scene_map:  # Only create entity if room has scenes
            entities.append(
                HueRoomSceneSelector(
                    hass=hass,
                    config_entry=config_entry,
                    room_name=room_name,
                    scene_map=scene_map,  # dict: friendly_name -> scene_name
                )
            )
    
    if entities:
        async_add_entities(entities, True)
        _LOGGER.info(f"Created {len(entities)} Hue Scene Selectors: {[e.name for e in entities]}")


class HueRoomSceneSelector(SelectEntity):
    """A select entity for choosing Hue scenes in a specific room."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:palette"

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        room_name: str,
        scene_map: dict[str, str],  # friendly_name -> scene_name
    ) -> None:
        """Initialize the scene selector."""
        self.hass = hass
        self._config_entry = config_entry
        self._room_name = room_name
        self._scene_map = scene_map  # Maps display names to actual scene names
        self._current_option: str | None = None
        
        # Generate clean identifiers
        room_slug = room_name.lower().replace(" ", "_")
        
        self._attr_unique_id = f"hue_scene_selector_{room_slug}"
        self._attr_name = f"{room_name} Scenes"
        self._attr_options = list(scene_map.keys())  # Friendly names for dropdown
        
        # Device info for grouping in the UI
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"hue_scene_selector_{room_slug}")},
            name=f"{room_name} Scene Selector",
            manufacturer="Philips Hue",
            model="Scene Selector",
            suggested_area=room_name,
        )

    @property
    def current_option(self) -> str | None:
        """Return the currently selected option."""
        return self._current_option

    async def async_select_option(self, option: str) -> None:
        """Handle the user selecting a scene."""
        self._current_option = option
        self.async_write_ha_state()
        
        # Get the actual scene name for the Hue bridge
        scene_name = self._scene_map.get(option, option)
        
        # Activate the Hue scene
        try:
            await self.hass.services.async_call(
                "hue",
                "hue_activate_scene",
                {
                    "group_name": self._room_name,
                    "scene_name": scene_name,
                },
                blocking=True,
            )
            _LOGGER.debug(f"Activated scene '{scene_name}' in room '{self._room_name}'")
        except Exception as err:
            _LOGGER.error(f"Failed to activate scene '{scene_name}' in '{self._room_name}': {err}")

    async def async_update(self) -> None:
        """Refresh the list of available scenes."""
        rooms_and_scenes = await self.hass.async_add_executor_job(
            get_hue_rooms_and_scenes, self.hass
        )
        
        if self._room_name in rooms_and_scenes:
            new_scene_map = rooms_and_scenes[self._room_name]
            if new_scene_map != self._scene_map:
                self._scene_map = new_scene_map
                self._attr_options = list(new_scene_map.keys())
                _LOGGER.debug(f"Updated scenes for {self._room_name}: {list(new_scene_map.keys())}")

