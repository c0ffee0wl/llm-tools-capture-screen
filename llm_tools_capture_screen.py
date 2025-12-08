"""
LLM tool for capturing screenshots using maim.

Works on X11-based Linux systems (Debian/Ubuntu/Kali/XFCE).
"""
import os
import shutil
import subprocess
import tempfile
import time
from typing import Optional

import llm


def _check_dependencies() -> Optional[str]:
    """Check if required tools are installed."""
    if not shutil.which('maim'):
        return "maim not installed. Install with: sudo apt install maim"
    return None


def _capture_full_screen(output_path: str, delay: int = 5, timeout: int = 10) -> Optional[str]:
    """Capture entire screen. Returns error message or None on success."""
    try:
        if delay > 0:
            time.sleep(delay)
        result = subprocess.run(
            ['maim', output_path],
            capture_output=True,
            timeout=timeout
        )
        if result.returncode != 0:
            return result.stderr.decode().strip() or "maim capture failed"
        return None
    except subprocess.TimeoutExpired:
        return "Screenshot timed out"
    except Exception as e:
        return str(e)


def _capture_window(output_path: str, delay: int = 5, timeout: int = 30) -> Optional[str]:
    """Capture user-selected window (click to select). Returns error message or None on success."""
    if not shutil.which('xdotool'):
        return "xdotool not installed. Install with: sudo apt install xdotool"

    try:
        # Delay before showing selection cursor
        if delay > 0:
            time.sleep(delay)

        # Let user click to select a window (cursor changes to crosshair)
        window_result = subprocess.run(
            ['xdotool', 'selectwindow'],
            capture_output=True,
            timeout=timeout
        )
        if window_result.returncode != 0:
            return "Window selection cancelled or failed"

        window_id = window_result.stdout.decode().strip()

        # Capture that window
        result = subprocess.run(
            ['maim', '-i', window_id, output_path],
            capture_output=True,
            timeout=10
        )
        if result.returncode != 0:
            return result.stderr.decode().strip() or "maim window capture failed"
        return None

    except subprocess.TimeoutExpired:
        return "Window selection timed out (30s)"
    except Exception as e:
        return str(e)


def capture_screen(mode: str = "window", delay: int = 5) -> llm.ToolOutput:
    """Capture a screenshot of a selected window or the entire screen.

ALWAYS use mode="window" unless the user explicitly says "entire screen" or "full screen".
Window mode lets the user click to select exactly which window to capture, which is
almost always what users want.

USE when the user asks to:
- See what's on their screen
- Capture a screenshot of a window or application
- Show a specific window or application
- Analyze visual content on the display

DO NOT use for:
- Terminal text content (inefficient for text)
- Wayland sessions (X11 only)
- Headless/SSH environments (requires display)

Args:
    mode: Capture mode - PREFER "window" over "full":
          - "window" (default, recommended): User clicks to select a window
          - "full": Entire screen - only use if user explicitly requests it
    delay: Seconds to wait before capturing (default 5, min 2, max 30).

Returns:
    ToolOutput with the screenshot as an attachment.
"""
    # Check dependencies
    dep_error = _check_dependencies()
    if dep_error:
        raise Exception(dep_error)

    # Validate delay (max 30s). Min 0 allowed for callers that handle delay themselves
    # (e.g., llm-sidechat shows countdown then passes delay=0). LLM should use min 2.
    delay = max(0, min(int(delay), 30))

    # Validate mode
    if mode not in ("full", "window"):
        mode = "window"

    # Create temp file
    temp_fd, temp_path = tempfile.mkstemp(suffix='.png', prefix='llm_screenshot_')
    os.close(temp_fd)

    try:
        # Capture based on mode
        if mode == "window":
            error = _capture_window(temp_path, delay=delay)
        else:
            error = _capture_full_screen(temp_path, delay=delay)

        if error:
            os.unlink(temp_path)
            raise Exception(f"Screenshot failed: {error}")

        # Verify file exists and has content
        if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise Exception("Screenshot file empty or not created")

        return llm.ToolOutput(
            output=f"Screenshot captured ({mode} mode, {delay}s delay)",
            attachments=[llm.Attachment(path=temp_path, type="image/png")]
        )

    except Exception:
        # Cleanup on any error
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


@llm.hookimpl
def register_tools(register):
    """Register the capture_screen tool with llm."""
    register(capture_screen)
