
from neo4j import GraphDatabase
import os

# Configuration from memory_manager.py
URI = "neo4j://127.0.0.1:7687"
AUTH = ("neo4j", "Sunkavalli06@")

def verify_connection():
    print(f"Connecting to {URI}...")
    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            driver.verify_connectivity()
            print("Connection successful!")
            
            # Get some stats
            with driver.session() as session:
                result = session.run("MATCH (n) RETURN count(n) as node_count")
                node_count = result.single()["node_count"]
                
                result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
                rel_count = result.single()["rel_count"]
                
                print(f"Graph Stats: {node_count} Nodes, {rel_count} Relationships")
                
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    verify_connection()
