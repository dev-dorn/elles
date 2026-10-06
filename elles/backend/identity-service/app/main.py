from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.infrastructure.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting identity-service | DB: postgres")
    # TODO: Initialize Async DB pools and RabbitMQ connections here
    yield
    print(f"Shutting down identity-service...")

app = FastAPI(
    title="Identity Service",
    description="Identity & Access (Users, Auth)",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "identity-service"}
