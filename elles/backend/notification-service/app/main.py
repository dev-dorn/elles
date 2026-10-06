from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.infrastructure.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting notification-service | DB: mongo")
    # TODO: Initialize Async DB pools and RabbitMQ connections here
    yield
    print(f"Shutting down notification-service...")

app = FastAPI(
    title="Notification Service",
    description="Notification & Shipping (Receipts, Emails)",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "notification-service"}
