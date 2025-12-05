import os
import uiautomation as auto
from mem0 import Memory
from interpreter import interpreter

print("--- TESTING SYSTEM STACK ---")

# 1. Test Windows Vision
print("[1/3] Testing Windows 'Eyes'...")
try:
    # This grabs the window under your mouse
    root = auto.GetRootControl()
    print(f"   Success! Root Resolution: {root.BoundingRectangle}")
except Exception as e:
    print(f"   FAIL: {e}")

# [2/3] Testing Memory Integration...
print("[2/3] Testing Memory Integration...")
try:
    # UPDATED CONFIG: Force everything to use Local Ollama
    config = {
        "llm": {
            "provider": "ollama",
            "config": {
                "model": "llama3.2",
                "temperature": 0
            }
        },
        "embedder": {
            "provider": "ollama",
            "config": {
                "model": "nomic-embed-text"
            }
        },
        "vector_store": {
            "provider": "chroma",
            "config": {
                "collection_name": "test_mem",
                "path": "db"
            }
        },
        "graph_store": {
            "provider": "neo4j",
            "config": {
                "url": "bolt://localhost:7687",
                "username": "neo4j",
                "password": "qwertyuiop"  # <--- Make sure this matches your Neo4j password
            }
        }
    }
    
    m = Memory.from_config(config)
    m.add("User wants to build a desktop agent.", user_id="test_user")
    print("   Success! Memory stored locally using Llama 3.2.")

except Exception as e:
    print(f"   FAIL: {e}")

# 3. Test The Planner (Open Interpreter)
print("[3/3] Testing Planner Import...")
try:
    # Just checking if it loads, not running it yet
    interpreter.offline = True 
    print("   Success! Interpreter loaded.")
except Exception as e:
    print(f"   FAIL: {e}")

print("--- DONE ---")