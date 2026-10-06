from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.infrastructure.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting inventory-service | DB: postgres")
    # TODO: Initialize Async DB pools and RabbitMQ connections here
    yield
    print(f"Shutting down inventory-service...")

app = FastAPI(
    title="Inventory Service",
    description="Inventory & Warehouse (Stock, Batches)",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "inventory-service"}
