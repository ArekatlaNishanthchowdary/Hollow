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
    Scans the active window for buttons/fields using recursive search
    to find nested elements (like 'File name' in Save As dialogs).
    """
    elements = []
    try:
        window = auto.GetForegroundControl()
    except:
        window = auto.GetRootControl()

    # Recursive helper to find relevant controls
    def walk(control, depth):
        if depth > 5: return # Depth limit to prevent lag
        
        children = control.GetChildren()
        for child in children:
            try:
                # We only care about interactable types usually found in dialogs
                # Edit = Text Box, Button = Button, ListItem = File/Folder
                if not child.IsOffscreen:
                    name = child.Name
                    ctype = child.ControlTypeName
                    
                    # Capture useful elements (Names, Inputs, Buttons)
                    if name or ctype in ["EditControl", "ButtonControl"]:
                        elements.append(f"Type:{ctype} | Name:'{name}'")
                    
                    # Recurse
                    walk(child, depth + 1)
            except:
                continue

    # Start recursion
    walk(window, 0)
            
    # De-duplicate and limit output size for LLM
    unique_elements = list(set(elements))
    # Sort for deterministic output
    unique_elements.sort()

    if not unique_elements:
        return "No interactable elements found."
    
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

def type_text(text: str):
    """
    Types text slowly to prevent typos like 'Observation est'.
    """
    time.sleep(1.0) # Wait for focus
    # SLOW DOWN TYPING: 0.1s per character (very safe)
    pyautogui.write(text, interval=0.1) 
    pyautogui.press('enter')
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

def press_hotkey(key_combo: str):
    """
    Performs a shortcut and WAITS for the popup (Critical for Ctrl+S).
    """
    keys = key_combo.split('+')
    pyautogui.hotkey(*keys)
    
    # CRITICAL FIX: Wait 3 seconds for 'Save As' dialogs
    print(f"   [Tool] Pressed {key_combo}, waiting 3s for UI...")
    time.sleep(3.0) 
    return f"Pressed shortcut: {key_combo}"

def get_user_folder_path(folder_name: str):
    """
    Returns absolute path to Desktop/Documents.
    """
    home = os.path.expanduser("~")
    path = os.path.join(home, folder_name)
    return path