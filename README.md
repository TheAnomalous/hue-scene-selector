# Hue Scene Selector

**Automatically creates dropdown selectors for every Hue room.**

No YAML. No typing scene names. Just install and go.

## What It Does

1. **Auto-discovers** all your Hue rooms/zones
2. **Creates a dropdown** (`select.bedroom_scenes`, `select.family_room_scenes`, etc.) for each room
3. **Populates scenes** automatically—no manual entry
4. **Updates dynamically** when you add/remove scenes in the Hue app
5. **Activates scenes** via the native `hue.hue_activate_scene` service

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add this repository URL and select "Integration"
4. Search for "Hue Scene Selector" and install
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/hue_scene_selector` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for "Hue Scene Selector"
3. Select your Hue bridge
4. Done! Dropdowns are created for each room.

## Usage

After setup, you'll have entities like:

- `select.bedroom_scenes`
- `select.family_room_scenes`
- `select.kitchen_scenes`

### Dashboard Card (Mushroom)

```yaml
type: custom:mushroom-select-card
entity: select.bedroom_scenes
name: Bedroom Scenes
icon: mdi:palette
layout: horizontal
```

### Standard Card

```yaml
type: entities
entities:
  - entity: select.bedroom_scenes
  - entity: select.family_room_scenes
```

## How It Works

This integration:

1. Scans all `scene.*` entities in Home Assistant
2. Matches them to Hue rooms by parsing entity IDs (e.g., `scene.bedroom_bright` → Bedroom)
3. Creates a `SelectEntity` for each room with that room's scenes as options
4. When you select a scene, it calls `hue.hue_activate_scene` with the correct room and scene names

## Requirements

- Home Assistant 2024.1.0 or newer
- Philips Hue integration already configured

## Troubleshooting

**No entities created?**
- Make sure the Hue integration is set up and scenes are visible in Developer Tools → States (search for `scene.`)

**Missing room?**
- The integration detects rooms by checking for a matching `light.*` entity. If your room doesn't have a light group, scenes won't be grouped correctly.

## License

MIT
