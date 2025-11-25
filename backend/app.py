# app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn
from contextlib import asynccontextmanager
from routes.routes import router
from routes.claim_routes import router as claim_router
from routes.hitl_routes import router as hitl_router
from routes.user_routes import router as user_router
from routes.auth_routes import router as auth_router
from routes.chat_routes import router as chat_router
from routes.metrics_routes import router as metrics_router
from routes.monitoring_routes import router as monitoring_router
from routes.feedback_routes import router as feedback_router
from sqlmodel import SQLModel
from models import *
from database import db_pool
from utils.config import (
    DB_POOL_MIN, 
    DB_POOL_MAX,
    API_HOST,
    API_PORT,
    RELOAD,
    get_cors_config,
)
from utils.gcp_clients import initialize_gcp_clients, gcp_clients

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger = logging.getLogger(__name__)
    
    # Startup
    logger.info("Initializing application...")
    
    # Initialize GCP clients first
    try:
        initialize_gcp_clients()
        logger.info("GCP clients initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize GCP clients: {e}")
        # If GCP is critical, uncomment the next line to prevent startup
        # raise
    
    # Initialize DB pool, repositories and agent
    db_pool.initialize_pool(minconn=DB_POOL_MIN, maxconn=DB_POOL_MAX)
    SQLModel.metadata.create_all(db_pool._engine)
    # initialize_repositories()
    # initialize_agent()
    
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    gcp_clients.close()
    db_pool.close_all_connections()
    logger.info("Application shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Claims Agent",
    redoc_url=None,
    # docs_url=None,
    lifespan=lifespan
)

# Configure CORS using config
app.add_middleware(
    CORSMiddleware,
    **get_cors_config()
)

# Include routers
app.include_router(router)  # Main processing routes
app.include_router(claim_router)  # Claim management routes
app.include_router(hitl_router)  # HITL queue routes
app.include_router(user_router)  # User management routes
app.include_router(auth_router)  # Authentication routes
app.include_router(chat_router)  # Chat assistant routes
app.include_router(metrics_router)  # Metrics validation routes (serves metrics_output.json)
app.include_router(monitoring_router)  # Monitoring data routes
app.include_router(feedback_router, prefix="/api/feedback", tags=["feedback"])  # Feedback routes

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=API_HOST,
        port=API_PORT,
        reload=RELOAD
    )