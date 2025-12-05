from memory_manager import MemoryJanitor
import time

print("--- TESTING MEMORY ALGORITHM ---")

# 1. Init
janitor = MemoryJanitor(user_id="test_runner")

# 2. Create Fake History (Simulating a long session)
fake_history = [
    "Step 1: Opened Start Menu",
    "Step 2: Typed 'Notepad'",
    "Step 3: Clicked 'Notepad' icon",
    "Step 4: Window 'Untitled - Notepad' focused",
    "Step 5: Typed 'Meeting notes for project'",
    "Step 6: Clicked File > Save",
    "Step 7: Typed filename 'notes.txt'"
]

print(f"\n[Input] Raw History Length: {len(fake_history)}")

# 3. Run Pruning
start_time = time.time()
pruned_history = janitor.prune_history(fake_history)
end_time = time.time()

# 4. Report
print(f"\n[Output] Pruned History Length: {len(pruned_history)}")
print(f"[Performance] Pruning took: {end_time - start_time:.2f} seconds")
print("\n--- NEW HISTORY STACK ---")
for item in pruned_history:
    print(item)