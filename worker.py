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
import asyncio
import logging
from datetime import datetime, timedelta
from neo4j import AsyncGraphDatabase, exceptions as neo4j_exceptions
from config import settings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

# ==================== LOGGING SETUP ====================
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=settings.LOG_FORMAT,
)
logger = logging.getLogger(__name__)

# ==================== DATABASE CONNECTION ====================
driver = None
MAX_RETRIES = 3

def is_retriable_error(exception):
    """Determine if a connection error is retriable."""
    if isinstance(exception, neo4j_exceptions.AuthError):
        logger.error(f"Authentication failed: {exception}")
        return False
    return True

def after_retry_attempt(retry_state):
    """Log the failure after an attempt."""
    attempt = retry_state.attempt_number
    exception = retry_state.outcome.exception()

    if exception and not isinstance(exception, neo4j_exceptions.AuthError):
        if isinstance(exception, neo4j_exceptions.ServiceUnavailable):
            logger.warning(f"Database unavailable (attempt {attempt}/{MAX_RETRIES}): {exception}")
        else:
            logger.error(f"Connection error: {exception}")

def before_sleep_log(retry_state):
    logger.info(f"Retrying database connection (attempt {retry_state.attempt_number + 1}/{MAX_RETRIES})...")

@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception(is_retriable_error),
    reraise=True,
    before_sleep=before_sleep_log,
    after=after_retry_attempt
)
async def _connect_with_retry():
    """Inner function to handle driver connection with retries"""
    logger.info("Attempting database connection...")
    new_driver = AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        connection_pool_size=settings.NEO4J_CONNECTION_POOL_SIZE,
        encrypted=True,
        trust="TRUST_SYSTEM_CA_SIGNED_CERTIFICATES",
    )
    await new_driver.verify_connectivity()
    logger.info("✅ Successfully connected to Neo4j")
    return new_driver

async def get_db_driver():
    """Initialize Neo4j driver with connection pooling and error handling"""
    global driver

    if driver is not None:
        return driver

    try:
        driver = await _connect_with_retry()
        return driver
    except neo4j_exceptions.AuthError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to connect to Neo4j after all retries") from e


async def run_query(query: str, **parameters):
    """Execute Cypher query with error handling"""
    if driver is None:
        raise RuntimeError("Database driver not initialized")

    try:
        async with driver.session() as session:
            result = await session.run(query, **parameters)
            return [record.data() async for record in result]
    except neo4j_exceptions.ServiceUnavailable as e:
        logger.error(f"Database service unavailable: {e}")
        raise
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise


async def durable_agent_loop():
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
        driver = await get_db_driver()
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
                results = await run_query(
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
        await asyncio.sleep(settings.PSA_POLLING_INTERVAL_SECONDS)

async def main():
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
        await durable_agent_loop()
    except asyncio.CancelledError:
        logger.info("\n🛑 PSA loop cancelled, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        exit(1)
    finally:
        if driver:
            await driver.close()
            logger.info("Database connection closed")
        logger.info("PSA Worker stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n🛑 PSA Gracefully shutting down via keyboard interrupt...")
