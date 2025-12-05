import ollama
from mem0 import Memory

# --- CONFIGURATION (Must match your test_stack.py) ---
config = {
    "llm": {
        "provider": "ollama",
        "config": {"model": "llama3.2", "temperature": 0}
    },
    "embedder": {
        "provider": "ollama",
        "config": {"model": "nomic-embed-text"}
    },
    "vector_store": {
        "provider": "chroma",
        "config": {"collection_name": "agent_memory", "path": "db"}
    },
    "graph_store": {
        "provider": "neo4j",
        "config": {
            "url": "bolt://localhost:7687",
            "username": "neo4j",
            "password": "qwertyuiop"  # <--- YOUR PASSWORD HERE
        }
    }
}

class MemoryJanitor:
    def __init__(self, user_id="main_agent"):
        print("   [Janitor] Initializing Memory Subsystem...")
        self.memory = Memory.from_config(config)
        self.user_id = user_id

    def add_long_term_memory(self, text):
        """Directly adds a fact/summary to the Graph."""
        self.memory.add(text, user_id=self.user_id)

    def retrieve_context(self, query):
        """Finds relevant past actions based on current goal."""
        # 1. Search Memory
        results = self.memory.search(query, user_id=self.user_id, limit=3)
        
        # --- CRITICAL FIX START ---
        # Handle new Mem0 response format (Dictionary with 'results' key)
        if isinstance(results, dict):
            if "results" in results:
                results = results["results"]
            else:
                # If it returns a dict but no results key, it might be an empty response or error
                results = []
        # --- CRITICAL FIX END ---

        # 2. Extract text payload
        # Now 'results' is guaranteed to be a List of dictionaries
        return [r['memory'] for r in results] if results else []

    def prune_history(self, raw_history):
        """
        THE CORE ALGORITHM:
        1. Checks if history is too long (> 5 steps).
        2. Compresses the oldest chunk using Llama 3.2.
        3. Stores summary in Graph.
        4. Returns pruned list.
        """
        THRESHOLD = 5
        
        if len(raw_history) <= THRESHOLD:
            return raw_history

        # Slice the oldest chunk (The stuff to compress)
        chunk_to_compress = raw_history[:THRESHOLD]
        remaining_history = raw_history[THRESHOLD:]

        print(f"   [Janitor] Pruning {len(chunk_to_compress)} steps...")

        # 1. Ask Llama 3.2 to Summarize
        prompt = f"""
        You are a backend process for an AI agent. 
        Compress the following list of GUI actions into a single factual sentence.
        Keep filenames, error codes, and app names.
        
        ACTIONS:
        {chunk_to_compress}
        
        SUMMARY:
        """
        
        response = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt}])
        summary = response['message']['content'].strip()

        print(f"   [Janitor] Generated Summary: '{summary}'")

        # 2. Store in Long-Term Memory (Graph)
        self.add_long_term_memory(summary)

        # 3. Return the new "Short-Term" history (Summary + Recent Actions)
        # We inject the summary as a text string so the Agent knows what happened previously
        new_history = [f"[Previous Context: {summary}]"] + remaining_history
        return new_history