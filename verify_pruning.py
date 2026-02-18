
from memory_manager import MemoryJanitor
import uuid
import time
from neo4j import GraphDatabase

# Config (Reuse from memory_manager)
URI = "neo4j://127.0.0.1:7687"
AUTH = ("neo4j", "Sunkavalli06@")

def verify_pruning():
    print("Initializing MemoryJanitor...")
    janitor = MemoryJanitor(user_id="test_pruner")
    
    session_id = str(uuid.uuid4())
    print(f"Test Session ID: {session_id}")
    
    # 1. Log 5 steps to trigger pruning
    for i in range(1, 6):
        step_data = {
            "session_id": session_id,
            "step_number": i,
            "action_type": "test_action",
            "description": f"This is step number {i} of the pruning test."
        }
        print(f"Logging Step {i}...")
        janitor.log_step_to_neo4j(step_data)
        time.sleep(1)

    # 2. Log 6th step to verify linking to summary
    print("Logging Step 6 (Should link to Summary)...")
    step_data = {
        "session_id": session_id,
        "step_number": 6,
        "action_type": "test_action",
        "description": "This is step 6, verifying link to summary."
    }
    janitor.log_step_to_neo4j(step_data)
        
    print("\n--- Verification ---")
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        # Check Summary Node
        result = session.run("MATCH (s:SummaryStep {end_step: 5})<-[:HAS_SUMMARY]-(sess:Session {id: $sid}) RETURN s.summary", sid=session_id)
        summary = result.single()
        if summary:
            print(f"SUCCESS: Summary Node found: '{summary[0]}'")
        else:
            print("FAILURE: Summary Node NOT found.")
            
        # Check Link
        result = session.run("""
            MATCH (sum:SummaryStep {end_step: 5})-[:NEXT]->(st:Step {step_number: 6})
            RETURN st
            """)
        if result.single():
            print("SUCCESS: Summary -> Step 6 link exists.")
        else:
            print("FAILURE: Link broken.")

if __name__ == "__main__":
    verify_pruning()
