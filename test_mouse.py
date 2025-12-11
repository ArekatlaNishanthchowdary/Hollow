import time
import pyautogui
import tools

print("--- AUTONOMOUS MOUSE TEST ---")
print("1. Opening Notepad...")
tools.open_app("notepad")
time.sleep(2)

print("2. Type 'Double Click Me'...")
tools.type_text("ClickMe")
time.sleep(1)

# Find where we are
x, y = pyautogui.position()
print(f"3. Moving mouse slightly away...")
pyautogui.moveTo(x - 50, y)
time.sleep(1)

print(f"4. Moving back and Double Clicking at ({x}, {y})...")
try:
    # Function from tools.py (now with interval=0.1)
    tools.click_element(x, y, double_click=True)
    print("Done. The text 'ClickMe' should be highlighted/selected.")
    print("Look at Notepad now!")
except Exception as e:
    print(f"Error: {e}")
