from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.infrastructure.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting catalog-service | DB: mongo")
    # TODO: Initialize Async DB pools and RabbitMQ connections here
    yield
    print(f"Shutting down catalog-service...")

app = FastAPI(
    title="Catalog Service",
    description="Catalog & Discovery (Products, Scent Notes)",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "catalog-service"}
