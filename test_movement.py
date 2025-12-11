import pyautogui
import time
import tools

print("--- EXTREME MOVEMENT TEST ---")
print("I am moving the mouse to (0, 0) - Top Left Corner in 3 seconds.")
time.sleep(3)

print("Moving...")
try:
    # Use direct pyautogui for raw test, avoiding tools.py wrappers to isolate logic
    pyautogui.moveTo(0, 0, duration=2.0)
    x, y = pyautogui.position()
    print(f"Ended at ({x}, {y})")
    
    if x == 0 and y == 0:
        print("SUCCESS: Reached (0,0)")
    else:
        print(f"FAIL: Landed at ({x}, {y}) instead of (0,0)")
        
except Exception as e:
    print(f"Error: {e}")
