# inventory_app/infrastructure/persistence/postgres/database.py
import logging
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from inventory_app.infrastructure.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.POSTGRES_URL,
    echo=False,
    pool_pre_ping=True,
)

# Create the async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def check_database_connection() -> bool:
    """Return whether PostgreSQL can execute a simple query."""
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        logger.exception("PostgreSQL health check failed")
        return False

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Dependency to yield an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def close_db_connection():
    """Called on app shutdown to cleanly close the engine."""
    await engine.dispose()
    logger.info("PostgreSQL connection closed.")
