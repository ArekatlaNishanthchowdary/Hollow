import pyautogui
import uiautomation as auto
import time
import os

# FAILSAFE: Drag mouse to corner to kill script
pyautogui.FAILSAFE = True

def get_screen_text_map():
    """
    Scans the active window for buttons/fields.
    """
    elements = []
    try:
        window = auto.GetForegroundControl()
    except:
        window = auto.GetRootControl()

    for count, control in enumerate(window.GetChildren()):
        if count > 50: break 
        try:
            name = control.Name
            if name and not control.IsOffscreen:
                elements.append(f"ID:{count} | Name:'{name}' | Type:{control.ControlTypeName}")
        except:
            continue
            
    if not elements:
        return "No interactable elements found."
    return "\n".join(elements)

def click_element(x: int, y: int, double_click: bool = False):
    """
    Moves mouse slowly and clicks.
    """
    # SLOW DOWN MOUSE: 1.0 second movement time
    pyautogui.moveTo(x, y, duration=1.0) 
    if double_click:
        pyautogui.doubleClick()
    else:
        pyautogui.click()
    return f"Clicked at ({x}, {y})"

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