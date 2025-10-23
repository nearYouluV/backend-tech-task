"""
FastAPI Application for Event Ingestion and Analytics

Основний модуль FastAPI додатку для збору подій та аналітики.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1 import events, stats, auth, cold_storage
from .core.config import settings
from .core.logging import setup_logging

from .middleware.rate_limit import RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifecycle events for the FastAPI application."""
    # Startup
    setup_logging()
    from .database.connection import init_db
    await init_db()
    yield
    # Shutdown
    pass


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Event Analytics API",
        description="API для збору подій та аналітики",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # Middleware
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # У продакшені слід обмежити
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health endpoint
    @app.get("/health")
    async def health():
        return {"status": "healthy", "message": "Service is running"}

    @app.get("/api/v1/health") 
    async def api_health():
        return {"status": "healthy", "version": "1.0.0", "message": "API is running"}

    # Routers
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(events.router, prefix="/api/v1")
    app.include_router(stats.router, prefix="/api/v1")
    app.include_router(cold_storage.router, prefix="/api/v1/cold-storage", tags=["Cold Storage Analytics"])

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
