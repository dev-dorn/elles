import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status

from inventory_app.infrastructure.config import settings
from inventory_app.infrastructure.persistence.postgres.database import (
    check_database_connection,
    close_db_connection,
)
from inventory_app.presentation.api import auth_check

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("inventory-service")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Starting inventory-service | env=%s", settings.ENVIRONMENT)
    try:
        if not await check_database_connection():
            raise RuntimeError("Could not connect to the inventory database")
        logger.info("PostgreSQL connection verified")
        yield
    finally:
        await close_db_connection()
        logger.info("Shutting down inventory-service")


app = FastAPI(title="Inventory Service", version="0.1.0", lifespan=lifespan)

app.include_router(auth_check.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    if not await check_database_connection():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Inventory database unavailable",
        )
    return {
        "status": "healthy",
        "service": "inventory-service",
        "database": "healthy",
    }
