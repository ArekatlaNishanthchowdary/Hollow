import ctypes

try:
    shcore = ctypes.windll.shcore
    user32 = ctypes.windll.user32

    print(f"System DPI: {user32.GetDpiForSystem()}")
    
    # Check awareness
    awareness = ctypes.c_int()
    shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness))
    print(f"Process Awareness Level: {awareness.value} (0=Unaware, 1=System, 2=PerMonitor)")

except Exception as e:
    print(f"Error checking DPI: {e}")
