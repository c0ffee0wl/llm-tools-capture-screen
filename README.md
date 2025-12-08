# llm-tools-capture-screen

LLM tool for capturing screenshots using maim on X11-based Linux systems.

## Installation

```bash
# Install system dependencies
sudo apt install maim xdotool

# Install the plugin
llm install /opt/llm-tools-capture-screen
```

## Usage

### Standalone with llm

```bash
# Full screen capture (5 second delay by default)
llm -T capture_screen "describe what's on my screen"

# Window selection (click to select)
llm --tool capture_screen '{"mode":"window"}' "what app is this?"

# Quick capture with shorter delay
llm --tool capture_screen '{"delay": 2}' "quick screenshot"

# Longer delay to arrange windows or open menus
llm --tool capture_screen '{"delay": 10}' "capture after I open the menu"

# Interactive chat with screenshot capability
llm chat -T capture_screen
```

### With llm-sidechat

The tool is automatically discovered when installed. The AI can call `capture_screen` during conversations.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mode` | string | `"full"` | Capture mode: `"full"` (entire screen) or `"window"` (click to select) |
| `delay` | int | `5` | Seconds to wait before capturing (0-60). Useful for arranging windows or capturing menus |

### Modes

- `mode="full"` (default): Captures the entire screen (all monitors)
- `mode="window"`: Shows crosshair cursor, click to select a window to capture

## Requirements

- X11 display server (XFCE, GNOME on X11, KDE on X11, etc.)
- `maim` - screenshot utility
- `xdotool` - X11 automation (for window selection)

## License

GPL-3.0
