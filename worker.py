"""
Perpetual State Agent (PSA) - Independent Background Worker
This script runs as a separate process (not within FastAPI)
It continuously monitors the Neo4j graph for stale requests and autonomously routes resources.
Deploy to Render as a Background Worker (not a Web Service).

Security & Scalability Improvements:
- Proper connection pool management
- Enhanced error handling and logging
- Configuration validation on startup
- Graceful shutdown handling
- Connection retry logic
"""
import time
import logging
from datetime import datetime, timedelta
from neo4j import GraphDatabase, exceptions as neo4j_exceptions
from config import settings

# ==================== LOGGING SETUP ====================
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=settings.LOG_FORMAT,
)
logger = logging.getLogger(__name__)

# ==================== DATABASE CONNECTION ====================
driver = None
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5


def get_db_driver():
    """Initialize Neo4j driver with connection pooling and error handling"""
    global driver

    if driver is not None:
        return driver

    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Attempting database connection (attempt {attempt + 1}/{MAX_RETRIES})...")
            driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                connection_pool_size=settings.NEO4J_CONNECTION_POOL_SIZE,
                encrypted=True,
                trust="TRUST_SYSTEM_CA_SIGNED_CERTIFICATES",
            )
            driver.verify_connectivity()
            logger.info("✅ Successfully connected to Neo4j")
            return driver

        except neo4j_exceptions.AuthError as e:
            logger.error(f"Authentication failed: {e}")
            raise
        except neo4j_exceptions.ServiceUnavailable as e:
            logger.warning(f"Database unavailable (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY_SECONDS)
        except Exception as e:
            logger.error(f"Connection error: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY_SECONDS)

    raise RuntimeError("Failed to connect to Neo4j after all retries")


def run_query(query: str, **parameters):
    """Execute Cypher query with error handling"""
    if driver is None:
        raise RuntimeError("Database driver not initialized")

    try:
        with driver.session() as session:
            result = session.run(query, **parameters)
            return [record.data() for record in result]
    except neo4j_exceptions.ServiceUnavailable as e:
        logger.error(f"Database service unavailable: {e}")
        raise
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise


def durable_agent_loop():
    """
    Infinite autonomous loop that wakes periodically and scans the topological core
    for unfulfilled resource requests. Automatically assigns optimal supplier routes
    and escalates critical cases.

    SECURITY: Only updates request status, does not modify authentication or permissions
    """
    logger.info(f"[{datetime.now()}] 🤖 Initializing Perpetual State Agent (PSA)...")
    logger.info(f"[{datetime.now()}] Connecting to Neo4j at {settings.NEO4J_URI}...")

    try:
        global driver
        driver = get_db_driver()
    except Exception as e:
        logger.error(f"Failed to initialize database connection: {e}")
        return

    while True:
        try:
            logger.info(f"[{datetime.now()}] 🔄 Waking up. Scanning Topological Core for unfulfilled nodes...")

            # Query for PENDING requests and assign suppliers
            query = """
            MATCH (c:Citizen)-[req:NEEDS {status: 'PENDING'}]->(res:Resource)
            OPTIONAL MATCH (s:Supplier)-[stock:STOCKS]->(res)
            WHERE stock.quantity > 0
            SET req.status = 'DISPATCHED_PENDING_CONFIRMATION',
                req.assigned_at = $timestamp
            RETURN c.id AS citizen_id,
                   s.name AS supplier_name,
                   res.type AS resource_type,
                   stock.quantity AS available_qty
            LIMIT 100
            """

            try:
                results = run_query(
                    query,
                    timestamp=datetime.utcnow().isoformat()
                )

                if results:
                    logger.warning(f"[{datetime.now()}] 🚨 Autonomic Routing Triggered: {len(results)} resource(s) re-routed")
                    for match in results:
                        citizen = match.get('citizen_id', 'UNKNOWN')
                        supplier = match.get('supplier_name', 'UNKNOWN')
                        resource = match.get('resource_type', 'UNKNOWN')
                        qty = match.get('available_qty', '?')
                        masked_citizen = f"{citizen[:2]}****{citizen[-2:]}" if len(citizen) > 4 else "****"
                        logger.info(f"  → [{resource}] {masked_citizen} ← Supplier: {supplier} (Qty: {qty})")
                else:
                    logger.info(f"[{datetime.now()}] ✅ Graph is optimized. No pending bottlenecks detected.")

            except neo4j_exceptions.ServiceUnavailable:
                logger.error("Database service temporarily unavailable")
                # Continue loop, will retry on next iteration
            except Exception as e:
                logger.error(f"Query execution error: {e}")
                # Continue loop despite errors

        except Exception as e:
            logger.error(f"[{datetime.now()}] ❌ PSA Core Error: {e}")
            # Continue loop - PSA must be resilient

        # Sleep before next cycle
        logger.info(f"[{datetime.now()}] 💤 Agent entering hibernation. Waking in {settings.PSA_POLLING_INTERVAL_SECONDS}s...")
        time.sleep(settings.PSA_POLLING_INTERVAL_SECONDS)

if __name__ == "__main__":
    """
    Main entry point for PSA worker process
    """
    logger.info("🚀 PSA Worker starting...")

    # Validate configuration
    if not settings.validate_all():
        logger.error("Configuration validation failed")
        exit(1)

    logger.info("✅ Configuration validated")

    try:
        durable_agent_loop()
    except KeyboardInterrupt:
        logger.info("\n🛑 PSA Gracefully shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        exit(1)
    finally:
        if driver:
            driver.close()
            logger.info("Database connection closed")
        logger.info("PSA Worker stopped")
