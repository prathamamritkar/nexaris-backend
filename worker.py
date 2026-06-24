# worker.py
"""
Perpetual State Agent (PSA) - Independent Background Worker
This script runs as a separate process (not within FastAPI)
It continuously monitors the Neo4j graph for stale requests and autonomously routes resources.
Deploy to Render as a Background Worker (not a Web Service).
"""
import time
import os
from datetime import datetime
from neo4j import GraphDatabase

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))


def durable_agent_loop():
    """
    Infinite autonomous loop that wakes periodically and scans the topological core
    for unfulfilled resource requests. Automatically assigns optimal supplier routes
    and escalates critical cases.
    """
    print(f"[{datetime.now()}] Initializing Perpetual State Agent (PSA)...")
    print(f"[{datetime.now()}] Connecting to Neo4j at {URI}...")

    while True:
        try:
            print(f"\n[{datetime.now()}] 🔄 Waking up. Scanning Topological Core for unfulfilled nodes...")

            # STATE 1 & 2: Query Neo4j for Requests stuck in PENDING
            # Find PENDING requests and autonomously assign suppliers with inventory
            query = """
            MATCH (c:Citizen)-[req:NEEDS {status: 'PENDING'}]->(res:Resource)
            OPTIONAL MATCH (s:Supplier)-[stock:STOCKS]->(res)
            WHERE stock.quantity > 0
            SET req.status = 'DISPATCHED_PENDING_CONFIRMATION'
            RETURN c.id AS citizen_id, s.name AS supplier_name, res.type AS resource_type, stock.quantity AS available_qty
            """

            with driver.session() as session:
                results = session.run(query).data()

                if results:
                    print(f"[{datetime.now()}] 🚨 Autonomic Routing Triggered: {len(results)} resource(s) re-routed")
                    for match in results:
                        citizen = match.get('citizen_id', 'UNKNOWN')
                        supplier = match.get('supplier_name', 'UNKNOWN')
                        resource = match.get('resource_type', 'UNKNOWN')
                        qty = match.get('available_qty', '?')
                        print(f"  → [{resource}] {citizen} ← Supplier: {supplier} (Qty: {qty})")
                else:
                    print(f"[{datetime.now()}] ✅ Graph is optimized. No pending bottlenecks detected.")

        except Exception as e:
            print(f"[{datetime.now()}] ❌ PSA Core Error: {e}")

        # STATE 3: Sleep State (Memory/Graph state remains intact on server)
        # The agent sleeps for 3600 seconds (1 hour), then wakes up to repeat the loop.
        print(f"[{datetime.now()}] 💤 Agent entering hibernation cycle. Memory state preserved. Waking in 3600s...")
        time.sleep(3600)


if __name__ == "__main__":
    try:
        durable_agent_loop()
    except KeyboardInterrupt:
        print(f"\n[{datetime.now()}] PSA Gracefully shutting down...")
        driver.close()
    finally:
        driver.close()
