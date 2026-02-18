
from memory_manager import MemoryJanitor
import time
import logging

# Enable debug logging for mem0
logging.basicConfig(level=logging.INFO)

def result_print(msg):
    print(f"\n[TEST] {msg}")

def verify_mem0():
    result_print("Initializing Janitor (mem0 + Neo4j)...")
    try:
        janitor = MemoryJanitor(user_id="test_user")
    except Exception as e:
        result_print(f"FAILED to initialize Janitor: {e}")
        return

    # 1. Get Initial Stats
    stats_before = janitor.get_memory_stats()
    result_print(f"Stats Before: {stats_before}")
    
    # 2. Add a Memory
    test_memory = f"User testing memory persistence {time.time()}. Verify Neo4j."
    result_print(f"Adding memory: '{test_memory}'")
    try:
        janitor.add_long_term_memory(test_memory)
        # mem0 might take a moment or be async? Usually sync.
    except Exception as e:
        result_print(f"FAILED to add memory: {e}")
        return

    # 3. Get Stats After
    stats_after = janitor.get_memory_stats()
    result_print(f"Stats After: {stats_after}")

    # 4. Verification of Vector Store
    result_print("Checking Vector Store via Search...")
    search_results = janitor.retrieve_context("User testing memory")
    result_print(f"Search Results: {search_results}")
    
    if search_results:
        result_print("SUCCESS: Vector Store is working.")
    else:
        result_print("WARNING: Vector Store returned empty results.")

    # 5. Verification of Graph
    nodes_diff = stats_after['nodes'] - stats_before['nodes']
    if nodes_diff > 0:
        result_print(f"SUCCESS: Graph grew by {nodes_diff} nodes.")
    else:
        result_print("WARNING: Graph node count did not increase. Graph extraction might have failed or is disabled.")

if __name__ == "__main__":
    verify_mem0()
