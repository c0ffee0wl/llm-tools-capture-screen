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
        return f"Screenshot timed out ({timeout}s)"
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
        if not window_id:
            return "Window selection returned empty ID"

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
        return f"Window selection timed out ({timeout}s)"
    except Exception as e:
        return str(e)


def _run_flameshot(output_path: str, flameshot_args: list, timeout: int) -> Optional[str]:
    """Run flameshot and move the saved file to output_path. Returns error or None."""
    temp_dir = tempfile.mkdtemp(prefix='llm_flameshot_')
    try:
        result = subprocess.run(
            ['flameshot', 'gui'] + flameshot_args + ['--path', temp_dir],
            capture_output=True,
            timeout=timeout
        )
        if result.returncode != 0:
            return result.stderr.decode().strip() or "flameshot capture failed or cancelled"

        # Find the saved file (flameshot generates its own filename)
        saved_files = [f for f in os.listdir(temp_dir) if f.endswith('.png')]
        if not saved_files:
            return "flameshot did not save a file (capture cancelled?)"

        # Move the file to the expected output path (remove pre-created empty file first)
        if os.path.exists(output_path):
            os.unlink(output_path)
        shutil.move(os.path.join(temp_dir, saved_files[0]), output_path)
        return None
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def _capture_region(output_path: str, delay: int = 5, timeout: int = 30) -> Optional[str]:
    """Capture user-selected region (draw rectangle to capture). Returns error or None."""
    if not shutil.which('flameshot'):
        return "flameshot not installed. Install with: sudo apt install flameshot"

    try:
        if delay > 0:
            time.sleep(delay)

        print(f"\033[33mDraw rectangle to select region ({timeout}s timeout)\033[0m", flush=True)
        return _run_flameshot(output_path, ['--accept-on-select'], timeout)
    except subprocess.TimeoutExpired:
        return f"Region capture timed out ({timeout}s)"
    except Exception as e:
        return str(e)


def _capture_annotate(output_path: str, delay: int = 5, timeout: int = 300) -> Optional[str]:
    """Capture region with annotation tools (draw, highlight, text, arrows). Returns error or None."""
    if not shutil.which('flameshot'):
        return "flameshot not installed. Install with: sudo apt install flameshot"

    try:
        if delay > 0:
            time.sleep(delay)

        timeout_min = timeout // 60
        print(f"\033[33mDraw rectangle, annotate, then click Accept ({timeout_min} min timeout)\033[0m", flush=True)
        return _run_flameshot(output_path, [], timeout)
    except subprocess.TimeoutExpired:
        return f"Annotation capture timed out ({timeout}s)"
    except Exception as e:
        return str(e)


def _capture_app(
    output_path: str,
    app_pattern: str,
    delay: int = 0,
    restore: str = "focus",
    search_by: str = "name"
) -> Optional[str]:
    """Capture a window by application name/class automatically (no user interaction).

    Generic internal function for capturing app windows. Finds the window matching
    the pattern, raises it briefly, captures, then restores focus.

    Args:
        output_path: Path to save the screenshot
        app_pattern: Pattern to match window (name or class depending on search_by)
        delay: Seconds to wait before capturing
        restore: How to handle window focus after capture:
            - "focus": Restore focus to original window (default)
            - "lower": Push target window behind others
            - "none": Leave target window raised
        search_by: How to search for window - "name" or "class"

    Returns:
        Error message string, or None on success.
    """
    if not shutil.which('xdotool'):
        return "xdotool not installed. Install with: sudo apt install xdotool"

    original_window = None
    target_window = None

    try:
        # Save current active window before any changes
        if restore == "focus":
            try:
                result = subprocess.run(
                    ['xdotool', 'getactivewindow'],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    original_window = result.stdout.decode().strip()
            except Exception:
                pass  # Continue even if we can't get original window

        # Find target window by name or class
        search_flag = '--name' if search_by == 'name' else '--class'
        search_result = subprocess.run(
            ['xdotool', 'search', '--limit', '1', search_flag, app_pattern],
            capture_output=True,
            timeout=5
        )
        search_output = search_result.stdout.decode().strip()
        if search_result.returncode != 0 or not search_output:
            return f"No window found matching {search_by} '{app_pattern}'"

        target_window = search_output.split('\n')[0]

        # Apply delay before capture
        if delay > 0:
            time.sleep(delay)

        # Raise the target window
        activate_result = subprocess.run(
            ['xdotool', 'windowactivate', '--sync', target_window],
            capture_output=True,
            timeout=5
        )
        if activate_result.returncode != 0:
            return f"Failed to activate window {target_window}"
        time.sleep(0.2)  # Brief pause for window to render

        # Capture the window
        result = subprocess.run(
            ['maim', '-i', target_window, output_path],
            capture_output=True,
            timeout=10
        )
        if result.returncode != 0:
            return result.stderr.decode().strip() or "maim capture failed"

        # Restore window state based on restore parameter
        if restore == "focus" and original_window:
            subprocess.run(
                ['xdotool', 'windowactivate', '--sync', original_window],
                capture_output=True,
                timeout=5
            )
        elif restore == "lower" and target_window:
            subprocess.run(
                ['xdotool', 'windowlower', target_window],
                capture_output=True,
                timeout=5
            )
        # restore == "none": do nothing, leave window raised

        return None

    except subprocess.TimeoutExpired:
        return "App capture timed out"
    except Exception as e:
        return str(e)


def _capture_rdp(output_path: str, restore: str = "focus") -> Optional[str]:
    """Capture Windows desktop via FreeRDP window automatically.

    Convenience wrapper around _capture_app for FreeRDP/Windows RDP sessions.
    If multiple RDP sessions exist, returns error with list of available sessions.

    No delay parameter - RDP capture is fully automatic with no user interaction,
    so delay would only slow things down unnecessarily.
    """
    if not shutil.which('xdotool'):
        return "xdotool not installed. Install with: sudo apt install xdotool"

    # First, check how many FreeRDP windows exist
    try:
        search_result = subprocess.run(
            ['xdotool', 'search', '--name', 'FreeRDP'],
            capture_output=True,
            timeout=5
        )
        search_output = search_result.stdout.decode().strip()
        if search_result.returncode != 0 or not search_output:
            return "No FreeRDP window found. Is xfreerdp running?"

        window_ids = search_output.split('\n')
        window_ids = [wid for wid in window_ids if wid]  # Filter empty strings

        if len(window_ids) > 1:
            # Multiple sessions - get their titles to help user identify them
            sessions = []
            for wid in window_ids:
                try:
                    name_result = subprocess.run(
                        ['xdotool', 'getwindowname', wid],
                        capture_output=True,
                        timeout=2
                    )
                    if name_result.returncode == 0:
                        sessions.append(name_result.stdout.decode().strip())
                except Exception:
                    sessions.append(f"Window {wid}")

            session_list = '\n  - '.join(sessions)
            return (
                f"Multiple FreeRDP sessions found ({len(window_ids)}). "
                f"Cannot auto-select:\n  - {session_list}\n"
                "Close extra sessions or use mode='window' to click-select."
            )

    except subprocess.TimeoutExpired:
        return "Timed out searching for FreeRDP windows"
    except Exception as e:
        return f"Error searching for FreeRDP windows: {e}"

    # Exactly one session - proceed with capture (delay=0 default, no waiting for automatic capture)
    error = _capture_app(
        output_path=output_path,
        app_pattern='FreeRDP',
        restore=restore,
        search_by='name'
    )
    return error


def capture_screen(mode: str = "window", delay: int = 5, restore: str = "focus") -> llm.ToolOutput:
    """Capture a screenshot of a window, region, or screen. Supports annotation/drawing.

ALWAYS use mode="window" unless the user explicitly requests something different:
- Use "rdp" when user wants to capture the FreeRDP/RDP window automatically (no clicking)
- Use "region" when user wants to capture just a portion/area of the screen
- Use "annotate" when user wants to draw, highlight, add arrows/text, or mark up a screenshot
- Use "full" only when user explicitly says "entire screen" or "full screen"

USE when the user asks to:
- See what's on their screen
- Capture a screenshot of a window or application
- Show a specific window or application
- Analyze visual content on the display
- Capture just a portion/region/area of the screen (use mode="region")
- Annotate, draw, highlight, circle something, add arrows or text (use mode="annotate")
- Capture the Windows RDP/remote desktop window automatically (use mode="rdp")

DO NOT use for:
- Terminal text content (inefficient for text)
- Wayland sessions (X11 only)
- Headless/SSH environments (requires display)

Args:
    mode: Capture mode:
          - "window" (default): User clicks to select a window to capture
          - "rdp": Automatically capture FreeRDP window showing a (mostly Windows) 
            remote desktop (no user interaction). Raises window briefly, captures, 
            then restores focus. Use when capturing Windows desktop/applications 
            via RDP without clicking.
          - "region": User draws rectangle to capture a screen region (uses flameshot)
          - "annotate": User draws rectangle, then can annotate with drawing tools,
            arrows, text, highlights, blur, etc. before saving (uses flameshot).
            Best when user wants to mark up, explain, or emphasize something visually.
          - "full": Entire screen - only use if user explicitly requests it
    delay: Seconds to wait before capturing (default 5, min 0, max 30).
          Ignored for "rdp" mode (automatic capture has no delay).
    restore: For "rdp" mode only - how to handle focus after capture:
          - "focus" (default): Return focus to the original window
          - "lower": Push RDP window behind other windows
          - "none": Leave RDP window raised/focused

Returns:
    ToolOutput with the screenshot as an attachment.
"""
    # Check dependencies
    dep_error = _check_dependencies()
    if dep_error:
        raise Exception(dep_error)

    # Validate delay (max 30s). Min 0 allowed for callers that handle delay themselves
    # (e.g., llm-sidechat shows countdown then passes delay=0). LLM should use min 2.
    try:
        delay = max(0, min(int(delay), 30))
    except (ValueError, TypeError):
        delay = 5  # Default if invalid

    # Validate mode
    if mode not in ("full", "window", "region", "annotate", "rdp"):
        mode = "window"

    # Validate restore parameter
    if restore not in ("focus", "lower", "none"):
        restore = "focus"

    # Create temp file
    temp_fd, temp_path = tempfile.mkstemp(suffix='.png', prefix='llm_screenshot_')
    os.close(temp_fd)

    try:
        # Capture based on mode
        if mode == "window":
            error = _capture_window(temp_path, delay=delay)
        elif mode == "rdp":
            error = _capture_rdp(temp_path, restore=restore)
        elif mode == "region":
            error = _capture_region(temp_path, delay=delay)
        elif mode == "annotate":
            error = _capture_annotate(temp_path, delay=delay)
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

        if mode == "rdp":
            output_msg = "Screenshot captured (rdp mode, automatic)"
        else:
            output_msg = f"Screenshot captured ({mode} mode, {delay}s delay)"

        return llm.ToolOutput(
            output=output_msg,
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
