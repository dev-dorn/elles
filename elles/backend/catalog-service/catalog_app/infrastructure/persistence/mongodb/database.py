from typing import AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from catalog_app.infrastructure.config import settings
import logging

logger = logging.getLogger(__name__)

# Create the async MongoDB client
client = AsyncIOMotorClient(settings.MONGODB_URL)

# Get the specific database
db: AsyncIOMotorDatabase = client[settings.MONGODB_DB_NAME]

async def get_mongodb_session() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """
    FastAPI Dependency to yield the MongoDB database instance.
    Motor handles connection pooling automatically.
    """
    yield db

async def close_mongodb_connection():
    """Called on app shutdown to cleanly close connections."""
    client.close()
    logger.info("MongoDB connection closed.")