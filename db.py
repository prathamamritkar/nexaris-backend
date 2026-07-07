import time
import logging
from neo4j import GraphDatabase, exceptions as neo4j_exceptions
from config import settings

logger = logging.getLogger(__name__)

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
            temp_driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                max_connection_pool_size=settings.NEO4J_CONNECTION_POOL_SIZE,
            )
            temp_driver.verify_connectivity()
            logger.info("✅ Successfully connected to Neo4j")
            if not settings.NEO4J_URI.startswith("neo4j+s") and not settings.NEO4J_URI.startswith("bolt+s"):
                logger.warning("⚠️ Warning: Connecting to Neo4j without strict encryption (not using neo4j+s/bolt+s)")
            driver = temp_driver
            return driver

        except neo4j_exceptions.AuthError as e:
            logger.error(f"Authentication failed: {e}")
            if 'temp_driver' in locals():
                temp_driver.close()
            raise
        except neo4j_exceptions.ServiceUnavailable as e:
            logger.warning(f"Database unavailable (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            if 'temp_driver' in locals():
                temp_driver.close()
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY_SECONDS)
        except Exception as e:
            logger.error(f"Connection error: {e}")
            if 'temp_driver' in locals():
                temp_driver.close()
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY_SECONDS)

    raise RuntimeError("Failed to connect to Neo4j after all retries")
