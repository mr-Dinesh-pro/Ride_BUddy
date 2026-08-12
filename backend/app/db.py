import logging
from neo4j import AsyncGraphDatabase
from app.config import settings

logger = logging.getLogger("ridebuddy.db")

class Neo4jConnectionManager:
    def __init__(self):
        self._driver = None

    async def connect(self):
        """Initializes the Neo4j Async Driver and verifies connection."""
        uri = settings.NEO4J_URI
        user = settings.NEO4J_USER
        password = settings.NEO4J_PASSWORD
        
        logger.info(f"Connecting to Neo4j at {uri} as user '{user}'...")
        try:
            self._driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
            # Run a lightweight query to verify connectivity on start
            async with self._driver.session() as session:
                await session.run("RETURN 1")
            logger.info("Successfully established connection to Neo4j/CognoDB.")
        except Exception as e:
            logger.error(f"Error connecting to Neo4j/CognoDB: {e}")
            self._driver = None
            raise RuntimeError(f"Database connection failed: {e}")

    async def close(self):
        """Closes the driver instance."""
        if self._driver:
            logger.info("Closing Neo4j/CognoDB connection driver...")
            await self._driver.close()
            self._driver = None
            logger.info("Neo4j/CognoDB connection closed.")

    def get_driver(self):
        if not self._driver:
            raise RuntimeError("Database connection is not initialized or is offline.")
        return self._driver

# Singleton instance of connection manager
db_manager = Neo4jConnectionManager()

async def get_db_session():
    """FastAPI Dependency to yield a Neo4j session and ensure cleanup."""
    driver = db_manager.get_driver()
    session = driver.session()
    try:
        yield session
    finally:
        await session.close()
