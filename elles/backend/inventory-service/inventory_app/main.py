from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from inventory_app.infrastructure.persistence.postgres.database import (
close_db_connection,
engine,
get_db_session,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("inventory_service")

@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection verified successfully")
    except SQLAlchemyError as e:
        logger.error(f"Failed to connect to the database on startup: {e}")
        raise
    logger.info(f"Starting inventory service | DB: inventory_db")
    yield

    logger.info("Shutting down inventory service..")
    await close_db_connection()

app = FastAPI(title="Inventory Service", version="1.0.0", lifespan=lifespan)

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db_session)):

    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except SQLAlchemyError:
        db_status = "unhealthy"
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": "inventory service",
        "database": db_status,
    }
