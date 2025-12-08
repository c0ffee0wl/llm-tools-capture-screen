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
# Window capture (default - click to select window)
llm -T capture_screen "describe what's in this window"

# Full screen capture
llm --tool capture_screen '{"mode":"full"}' "describe what's on my screen"

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
| `mode` | string | `"window"` | Capture mode: `"window"` (click to select) or `"full"` (entire screen) |
| `delay` | int | `5` | Seconds to wait before capturing (2-30). Useful for arranging windows or capturing menus |

### Modes

- `mode="window"` (default): Shows crosshair cursor, click to select a window to capture
- `mode="full"`: Captures the entire screen (all monitors)

## Requirements

- X11 display server (XFCE, GNOME on X11, KDE on X11, etc.)
- `maim` - screenshot utility
- `xdotool` - X11 automation (for window selection)

## License

GPL-3.0
