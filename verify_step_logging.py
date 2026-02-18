
from memory_manager import MemoryJanitor
import uuid
import time

def verify_step_logging():
    print("Initializing MemoryJanitor...")
    janitor = MemoryJanitor(user_id="test_logger")
    
    session_id = str(uuid.uuid4())
    print(f"Test Session ID: {session_id}")
    
    # Simulate 3 steps
    steps = [
        {"action": "thought", "desc": "Planning to open notepad"},
        {"action": "tool_call", "desc": "Opening Notepad"},
        {"action": "observation", "desc": "Notepad opened successfully"}
    ]
    
    for i, step in enumerate(steps):
        step_data = {
            "session_id": session_id,
            "step_number": i + 1,
            "action_type": step["action"],
            "description": step["desc"]
        }
        print(f"Logging step {i+1}...")
        janitor.log_step_to_neo4j(step_data)
        time.sleep(1) # Ensure timestamps differ slightly
        
    print("\n--- Verification ---")
    print("Please check Neo4j Browser with: MATCH (s:Session {id: '" + session_id + "'})-[:HAS_STEP]->(st) RETURN s, st ORDER BY st.step_number")

if __name__ == "__main__":
    verify_step_logging()
