import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from inventory_app.infrastructure.config import settings
from inventory_app.presentation.api import auth_check

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("inventory-service")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Starting inventory-service | env=%s", settings.ENVIRONMENT)
    yield
    logger.info("shutting down inventory-service...")


app = FastAPI(title="Inventory Service", version="0.1.0", lifespan=lifespan)

app.include_router(auth_check.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "inventory-service"}