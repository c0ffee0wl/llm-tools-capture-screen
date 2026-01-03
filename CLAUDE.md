# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an LLM tool plugin for capturing screenshots on X11-based Linux systems. It integrates with the [llm](https://llm.datasette.io/) CLI tool and provides a `capture_screen` tool that can be used in LLM conversations. Supports window capture, region selection, annotation/drawing, and automatic RDP window capture.

## Development Commands

```bash
# Install dependencies and the plugin in development mode
llm install -e /opt/llm-tools-capture-screen

# System dependencies required
sudo apt install maim xdotool flameshot

# Test the tool manually
llm -T capture_screen "describe what's in this window"
llm --tool capture_screen '{"mode":"window_id", "window_id":"0x2a00003"}' "capture this specific window"
llm --tool capture_screen '{"mode":"rdp"}' "capture the RDP window"
llm --tool capture_screen '{"mode":"region"}' "capture this region"
llm --tool capture_screen '{"mode":"annotate"}' "annotate and capture"
llm --tool capture_screen '{"mode":"full"}' "describe the screen"
```

## Architecture

Single-file plugin (`llm_tools_capture_screen.py`) using the llm plugin system:

- **Plugin registration**: Uses `@llm.hookimpl` decorator on `register_tools()` to register with llm
- **Entry point**: Defined in `pyproject.toml` under `[project.entry-points.llm]`
- **Tool output**: Returns `llm.ToolOutput` with PNG attachment via `llm.Attachment`

### Capture Modes

- `window` (default): Uses `xdotool selectwindow` then `maim -i <window_id>` - user clicks to select
- `window_id`: Capture specific window by X11 ID (no user interaction). Requires `window_id` parameter (hex like "0x2a00003" or decimal). Get IDs from `<gui_context>` block. Has `restore` parameter: "focus" (default) brings window to front, "none" captures as-is.
- `rdp`: Automatically finds FreeRDP window via `xdotool search --name FreeRDP`, raises it, captures with `maim -i`, restores focus. No user interaction needed. Has `restore` parameter: "focus" (default), "lower", "none"
- `region`: Uses `flameshot gui --accept-on-select` - user draws rectangle, captures immediately
- `annotate`: Uses `flameshot gui` - user draws rectangle, can annotate with drawing tools, then saves
- `full`: Uses `maim` directly for entire screen capture

### Key Constraints

- X11 only (not Wayland compatible)
- Delay parameter: 0-30 seconds (0 allowed for callers handling delay externally like llm-sidechat)
- Timeouts: window 30s, region 30s, annotate 5 min (for drawing/annotation)
- Flameshot modes print timeout warning to stdout before blocking
- Screenshots saved as temporary PNG files, cleaned up on error
