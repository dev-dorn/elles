from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from starlette.responses import JSONResponse

from catalog_app.domain.exceptions import DomainException
from catalog_app.infrastructure.config import settings
from catalog_app.infrastructure.persistence.mongodb.database import close_mongodb_connection
from catalog_app.presentation.api import products
from fastapi import Request

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger = logging.getLogger("catalog-service")
    logger.info(f"Starting catalog-service | DB: {settings.MONGODB_DB_NAME}")
    yield
    logger.info("shutting down catalog-service...")
    await close_mongodb_connection()

app = FastAPI(title="Catalog Service", version="1.0.0", lifespan=lifespan)
@app.exception_handler(DomainException)
async def duplicate_product_handler(_request: Request, exc: DomainException):
    return  JSONResponse(status_code=409, content={"detail": str(exc)})

@app.exception_handler(DomainException)
async def domain_error_handler(_request: Request, exc: DomainException):
    return JSONResponse(status_code=400, content={"detail": str(exc)})

app.include_router(products.router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "catalog-service"}




