import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import db_manager
from app.routes.rides import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ridebuddy.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown events for the database driver."""
    logger.info("Initializing application startup sequence...")
    try:
        await db_manager.connect()
    except Exception as e:
        logger.error(f"Could not connect to Neo4j during startup: {e}")
        logger.warning("The application is starting in a degraded state without database access.")
    
    yield
    
    logger.info("Initializing application shutdown sequence...")
    await db_manager.close()

# Create FastAPI app
app = FastAPI(
    title="Hyderabad Ride Sharing Matcher API",
    description="FastAPI Backend for traversing route paths and finding overlapping ride sharing matches in Hyderabad.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
# Allows requests from Vite (default local port 5173) and deployment urls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes directly to root level as per specification
app.include_router(router)

@app.get("/")
async def root():
    """Root endpoint for health and server status check."""
    db_status = "Online" if db_manager._driver is not None else "Offline"
    return {
        "app": "Hyderabad Local Ride Sharing Matcher API",
        "status": "Running",
        "database_status": db_status
    }
