import os
from dotenv import load_dotenv
import ollama
from mem0 import Memory

load_dotenv()

# --- CONFIGURATION (Must match your test_stack.py) ---
config = {
    "llm": {
        "provider": "ollama",
        "config": {
            "model": "llama3.1",
            "temperature": 0
        }
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
            "url": "neo4j://127.0.0.1:7687",
            "username": "neo4j",
            "password": "Sunkavalli06@"  # <--- YOUR PASSWORD HERE
        }
    }
}

# --- NEO4J DIRECT CONNECTION ---
from neo4j import GraphDatabase
NEO4J_URI = config["graph_store"]["config"]["url"]
NEO4J_AUTH = (config["graph_store"]["config"]["username"], config["graph_store"]["config"]["password"])

class MemoryJanitor:
    def __init__(self, user_id="main_agent"):
        print("   [Janitor] Initializing Memory Subsystem...")
        self.memory = Memory.from_config(config)
        self.user_id = user_id

    def get_memory_stats(self):
        """Returns stats about the Graph (Long-term Memory)."""
        stats = {"nodes": 0, "relationships": 0}
        try:
            with GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH) as driver:
                driver.verify_connectivity()
                with driver.session() as session:
                    # Count Nodes
                    result = session.run("MATCH (n) RETURN count(n) as node_count")
                    stats["nodes"] = result.single()["node_count"]
                    
                    # Count Relationships
                    result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
                    stats["relationships"] = result.single()["rel_count"]
        except Exception as e:
            print(f"   [Janitor] Error fetching stats: {e}")
        return stats

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

    def consolidate_last_5_steps(self, session_id, current_step_number):
        """
        Compresses the last 5 steps into a single SummaryStep and removes the raw nodes.
        """
        print(f"   [Janitor] Consolidating steps for Session {session_id}...")
        
        start_step = current_step_number - 4
        end_step = current_step_number
        
        try:
            with GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH) as driver:
                # 1. Fetch the steps to summarize
                query_fetch = """
                MATCH (s:Session {id: $sid})-[:HAS_STEP]->(st:Step)
                WHERE st.step_number >= $start AND st.step_number <= $end
                RETURN st.description as desc, st.action_type as type, st.step_number as num
                ORDER BY st.step_number
                """
                records = driver.execute_query(query_fetch, sid=session_id, start=start_step, end=end_step)[0]
                
                if not records:
                    print("   [Janitor] No steps found to consolidate.")
                    return

                # 2. Generate Summary
                text_to_compress = "\n".join([f"Step {r['num']} ({r['type']}): {r['desc']}" for r in records])
                prompt = f"""
                Summarize these 5 agent steps into one concise sentence. 
                Focus on the outcome.
                STEPS:
                {text_to_compress}
                SUMMARY:
                """
                response = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt}])
                summary_text = response['message']['content'].strip()
                print(f"   [Janitor] Cluster Summary: {summary_text}")

                # 3. Replace in Graph (Atomic Transaction)
                query_replace = """
                MATCH (s:Session {id: $sid})
                MATCH (s)-[:HAS_STEP]->(st:Step)
                WHERE st.step_number >= $start AND st.step_number <= $end
                WITH s, collect(st) as steps
                
                // Create Summary Node
                CREATE (sum:SummaryStep {
                    summary: $summary,
                    start_step: $start, 
                    end_step: $end,
                    timestamp: timestamp()
                })
                MERGE (s)-[:HAS_SUMMARY]->(sum)

                // Fix the finding of the previous node to link TO the new summary
                // We find whatever node was pointing to the FIRST step of our cluster
                WITH s, steps, sum
                MATCH (prev)-[:NEXT]->(first_step)
                WHERE first_step IN steps
                MERGE (prev)-[:NEXT]->(sum)

                // Delete old steps
                FOREACH (st IN steps | DETACH DELETE st)
                """
                driver.execute_query(query_replace, sid=session_id, start=start_step, end=end_step, summary=summary_text)
                print(f"   [Janitor] Pruned Steps {start_step}-{end_step}.")

        except Exception as e:
            print(f"   [Janitor] Consolidation Failed: {e}")

    def log_step_to_neo4j(self, step_data):
        """
        Logs a granular step to Neo4j.
        Expected step_data: {
            "session_id": str,
            "step_number": int,
            ...
        }
        """
        query = """
        MERGE (s:Session {id: $session_id})
        CREATE (st:Step {
            step_number: $step_number,
            action_type: $action_type,
            description: $description,
            timestamp: timestamp()
        })
        MERGE (s)-[:HAS_STEP]->(st)
        """
        
        # Link to previous step (Step OR SummaryStep)
        if step_data.get("step_number", 0) > 1:
            query += """
            WITH s, st
            MATCH (prev)
            WHERE (prev:Step AND prev.step_number = $step_number - 1)
               OR (prev:SummaryStep AND prev.end_step = $step_number - 1)
            MERGE (prev)-[:NEXT]->(st)
            """

        try:
             with GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH) as driver:
                driver.execute_query(
                    query, 
                    session_id=step_data["session_id"],
                    step_number=step_data["step_number"],
                    action_type=step_data["action_type"],
                    description=step_data["description"],
                    database_="neo4j"
                )
                print(f"   [Janitor] Logged Step {step_data['step_number']} to Neo4j.")
                
                # TRIGGER PRUNING every 5 steps
                if step_data['step_number'] % 5 == 0:
                    self.consolidate_last_5_steps(step_data["session_id"], step_data["step_number"])

        except Exception as e:
            print(f"   [Janitor] Failed to log step to Neo4j: {e}")