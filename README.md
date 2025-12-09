# llm-tools-capture-screen

LLM tool for capturing screenshots on X11-based Linux systems. Supports window capture, region selection, annotation/drawing, and automatic RDP window capture.

## Installation

```bash
# Install system dependencies
sudo apt install maim xdotool flameshot

# Install the plugin
llm install /opt/llm-tools-capture-screen
```

## Usage

### Standalone with llm

```bash
# Window capture (default - click to select window)
llm -T capture_screen "describe what's in this window"

# RDP capture (automatically find and capture FreeRDP window)
llm --tool capture_screen '{"mode":"rdp"}' "show me the Windows desktop"

# Region capture (draw rectangle to select area)
llm --tool capture_screen '{"mode":"region"}' "capture this part of the screen"

# Annotate mode (draw, highlight, add arrows/text before saving)
llm --tool capture_screen '{"mode":"annotate"}' "let me mark up what I'm seeing"

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
| `mode` | string | `"window"` | Capture mode: `"window"`, `"rdp"`, `"region"`, `"annotate"`, or `"full"` |
| `delay` | int | `5` | Seconds to wait before capturing (0-30). Useful for arranging windows or capturing menus |
| `restore` | string | `"focus"` | For `rdp` mode only: `"focus"` (restore original window), `"lower"` (push RDP behind), `"none"` (leave RDP raised) |

### Modes

- `mode="window"` (default): Shows crosshair cursor, click to select a window to capture
- `mode="rdp"`: Automatically find and capture FreeRDP window (no user interaction). Raises window, captures, then restores focus
- `mode="region"`: Draw a rectangle to capture a screen region (uses flameshot)
- `mode="annotate"`: Draw a rectangle, then annotate with drawing tools, arrows, text, highlights, blur before saving (uses flameshot)
- `mode="full"`: Captures the entire screen (all monitors)

## Requirements

- X11 display server (XFCE, GNOME on X11, KDE on X11, etc.)
- `maim` - screenshot utility (for window/full modes)
- `xdotool` - X11 automation (for window selection)
- `flameshot` - interactive screenshot with annotation (for region/annotate modes)

## License

GPL-3.0
