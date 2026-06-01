"""
main.py
-------
The FastAPI application entry point.

This file:
1. Creates the FastAPI app instance
2. Adds middleware (CORS, rate limiting, request logging)
3. Registers all routers (URL prefixes and endpoint groups)
4. Defines startup/shutdown events (connecting to Redis)
5. Adds the /health endpoint

Think of this like the main index.js in an Express app.
"""

import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.config import get_settings
from app.database import engine, get_db
from app.redis import get_redis_client, close_redis
from app.utils.logger import logger
from app.routers import auth, articles, tags, comments, bookmarks, admin

settings = get_settings()

# Rate limiter using the client's IP address as the key
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager - runs code on startup and shutdown.
    This replaces the older @app.on_event("startup") decorator.
    
    Code BEFORE 'yield' runs on startup.
    Code AFTER 'yield' runs on shutdown.
    """
    # Startup: connect to Redis
    logger.info("Starting up Team Knowledge Base API...")
    await get_redis_client()
    logger.info("Redis connection established.")
    yield
    # Shutdown: close Redis connection
    logger.info("Shutting down...")
    await close_redis()


# Create the FastAPI application
app = FastAPI(
    title="Team Knowledge Base API",
    description=(
        "A RESTful API for a shared team knowledge base. "
        "Team members can publish articles, organize with tags, "
        "bookmark favorites, and leave comments."
    ),
    version="1.0.0",
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc UI
    lifespan=lifespan,
)

# Rate limiting - attach the limiter to the app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware - controls which frontend origins can call this API
# In production, restrict this to your actual frontend domain(s)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware - logs every request with a unique ID
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware that runs for EVERY request.
    Adds a unique request_id for tracing, logs start/end, and measures duration.
    """
    request_id = str(uuid.uuid4())[:8]  # Short unique ID
    logger.info(f"[{request_id}] {request.method} {request.url.path} started")
    start_time = time.time()

    response = await call_next(request)

    duration = (time.time() - start_time) * 1000  # Convert to milliseconds
    logger.info(
        f"[{request_id}] {request.method} {request.url.path} "
        f"completed in {duration:.1f}ms -> {response.status_code}"
    )
    response.headers["X-Request-ID"] = request_id
    return response


# Register all routers under the /api/v1 prefix
API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(articles.router, prefix=API_PREFIX)
app.include_router(tags.router, prefix=API_PREFIX)
app.include_router(comments.router, prefix=API_PREFIX)
app.include_router(bookmarks.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)


# Health check endpoint - used by Docker Compose to verify the app is running
@app.get("/health", tags=["Health"])
@limiter.exempt  # Health checks should never be rate limited
async def health_check():
    """
    Verify that the API, PostgreSQL, and Redis are all healthy.
    Returns 200 if everything is OK, 503 if any dependency is down.
    """
    health = {"status": "healthy", "database": "unknown", "redis": "unknown"}

    # Check PostgreSQL
    try:
        async for db in get_db():
            await db.execute(text("SELECT 1"))
        health["database"] = "healthy"
    except Exception as e:
        health["database"] = f"unhealthy: {str(e)}"
        health["status"] = "degraded"

    # Check Redis
    try:
        redis = await get_redis_client()
        await redis.ping()
        health["redis"] = "healthy"
    except Exception as e:
        health["redis"] = f"unhealthy: {str(e)}"
        health["status"] = "degraded"

    status_code = 200 if health["status"] == "healthy" else 503
    return JSONResponse(content=health, status_code=status_code)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - redirects to docs."""
    return {
        "message": "Team Knowledge Base API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }
