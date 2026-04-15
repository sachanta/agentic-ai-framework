"""
Agentic AI Framework - Main FastAPI Application
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings
from app.core.middleware import setup_middleware
from app.db.mongodb import connect_mongodb, close_mongodb, init_default_data
from app.db.weaviate import connect_weaviate, close_weaviate
from app.platforms.hello_world import register_platform as register_hello_world
from app.platforms.newsletter import register_platform as register_newsletter

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")

    # Register platforms
    logger.info("Registering platforms...")
    register_hello_world()
    register_newsletter()
    logger.info("Platforms registered")

    # Connect to MongoDB (required)
    try:
        await connect_mongodb()
        # Initialize default data (creates admin/user accounts)
        await init_default_data()
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

    # Connect to Weaviate (optional)
    try:
        await connect_weaviate()
    except Exception as e:
        logger.warning(f"Weaviate connection failed (non-critical): {e}")

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await close_mongodb()
    await close_weaviate()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="A framework for building multi-agent AI applications",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup custom middleware
setup_middleware(app)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Mount MCP SSE server (graceful degradation if mcp not installed)
try:
    from app.mcp.sse import create_mcp_sse_app

    app.mount("/mcp", create_mcp_sse_app())
    logger.info("MCP SSE server mounted at /mcp")
except ImportError:
    logger.info("MCP package not installed — MCP SSE endpoint disabled")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_PREFIX}/docs",
        "health": f"{settings.API_V1_PREFIX}/health",
    }


@app.get("/health")
async def health():
    """Quick health check endpoint."""
    return {"status": "ok"}
