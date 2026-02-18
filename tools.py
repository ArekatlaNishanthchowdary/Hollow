import pyautogui
import uiautomation as auto
import time
import os
import ctypes

# FORCE DPI AWARENESS
# This fixes issues where coordinates are off by 125% or 150% on scaling screens
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()

# FAILSAFE: Drag mouse to corner to kill script
pyautogui.FAILSAFE = True

def get_screen_text_map():
    """
    Scans only the ACTIVE window for buttons/fields.
    Prevents reading background apps or the entire desktop.
    """
    elements = []
    try:
        # Get the specific element that has focus
        focused = auto.GetForegroundControl()
        # Climb up to the main Window (e.g., Notepad) so we see the whole app, not just the cursor
        window = focused.GetTopLevelControl()
        
        window_title = window.Name
        elements.append(f"Active Window: '{window_title}'")
    except Exception as e:
        return f"Error finding active window: {e}"

    # Recursive helper to find relevant controls
    def walk(control, depth):
        if depth > 5: return # Depth limit to prevent lag
        
        try:
            children = control.GetChildren()
        except:
            return

        for child in children:
            try:
                # We only care about interactable types usually found in dialogs
                # Edit = Text Box, Button = Button, ListItem = File/Folder
                if not child.IsOffscreen:
                    name = child.Name
                    ctype = child.ControlTypeName
                    
                    # Capture useful elements (Names, Inputs, Buttons)
                    if name or ctype in ["EditControl", "ButtonControl", "WindowControl"]:
                        # Skip generic intermediate containers to save tokens
                        if ctype == "PaneControl" and not name:
                            pass
                        else:
                            elements.append(f"Type:{ctype} | Name:'{name}'")
                    
                    # Recurse
                    walk(child, depth + 1)
            except:
                continue

    # Start recursion from the Top Level Window
    if window:
        walk(window, 0)
            
    # De-duplicate and limit output size for LLM
    unique_elements = list(set(elements))
    # Sort for deterministic output
    unique_elements.sort()

    if not unique_elements:
        return f"Active Window '{window_title}' found, but no interactables visible."
    
    # Cap at 100 lines to fit context
    return "\n".join(unique_elements[:100])

def click_element(x: int, y: int, double_click: bool = False):
    """
    Moves mouse slowly and clicks, with position verification.
    """
    start_x, start_y = pyautogui.position()
    print(f"   [Mouse] Starting at ({start_x}, {start_y}), Target: ({x}, {y})")
    
    # SLOW DOWN MOUSE: 1.0 second movement time
    pyautogui.moveTo(x, y, duration=1.0) 
    
    # VERIFY ARRIVAL
    end_x, end_y = pyautogui.position()
    if abs(end_x - x) > 5 or abs(end_y - y) > 5:
        print(f"   [Mouse] WARNING: Landed at ({end_x}, {end_y}) instead of ({x}, {y})")
        # Retry once
        pyautogui.moveTo(x, y, duration=0.5)
    
    if double_click:
        pyautogui.doubleClick(interval=0.1)
    else:
        pyautogui.click()
        
    return f"Moved from ({start_x}, {start_y}) to ({x}, {y}) and Clicked"

def type_text(text: str, press_enter: bool = True):
    """
    Types text slowly to prevent typos like 'Observation est'.
    """
    time.sleep(1.0) # Wait for focus
    # Fix: Remove double slashes if present (common LLM artifact)
    text = text.replace('\\\\', '\\')

    # SLOW DOWN TYPING: 0.1s per character (very safe)
    pyautogui.write(text, interval=0.1) 
    
    if press_enter:
        pyautogui.press('enter')
        return f"Typed '{text}' and pressed Enter"
    else:
        return f"Typed '{text}'"

def open_app(app_name: str):
    """
    Launches an app via Run.
    """
    pyautogui.hotkey('win', 'r')
    time.sleep(1.0)
    pyautogui.write(app_name)
    pyautogui.press('enter')
    # WAIT 3 SECONDS for the app to actually load
    time.sleep(3.0) 
    return f"Launched {app_name}"

def press_hotkey(key_combo: str = None, hotkey: str = None, keys: str = None):
    """
    Performs a shortcut and WAITS for the popup (Critical for Ctrl+S).
    Accepts various argument names to be robust against LLM hallucinations.
    """
    # Resolve the actual key combo from potential aliases
    actual_combo = key_combo or hotkey or keys
    if not actual_combo:
        return "Error: No key combination provided (expected 'key_combo', 'hotkey', or 'keys')"

    keys = actual_combo.split('+')
    pyautogui.hotkey(*keys)
    
    # CRITICAL FIX: Wait 3 seconds for 'Save As' dialogs
    print(f"   [Tool] Pressed {actual_combo}, waiting 3s for UI...")
    time.sleep(3.0) 
    return f"Pressed shortcut: {actual_combo}"

def get_user_folder_path(folder_name: str):
    """
    Returns absolute path to Desktop/Documents.
    """
    home = os.path.expanduser("~")
    path = os.path.join(home, folder_name)
    return path