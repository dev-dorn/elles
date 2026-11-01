# inventory_app/infrastructure/persistence/postgres/database.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from inventory_app.infrastructure.config import settings
import logging

logger = logging.getLogger(__name__)

# Create the async engine
engine = create_async_engine(settings.POSTGRES_URL, echo=False, pool_pre_ping=True)

# Create the async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Dependency to yield an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError:
            await session.rollback()
            raise
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def close_db_connection():
    """Called on app shutdown to cleanly close the engine."""
    await engine.dispose()
    logger.info("PostgreSQL connection closed.")