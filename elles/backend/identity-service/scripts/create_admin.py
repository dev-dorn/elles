# scripts/create_admin.py
import asyncio
import sys

sys.path.append('../../..')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.infrastructure.persistence.postgres.models import Base, AdminUserModel
from app.infrastructure.security.password_hasher import BcryptPasswordHasherAdapter
from app.infrastructure.config import settings
from uuid import uuid4


async def create_initial_admin():
    """Creates the initial admin user in the database."""

    # Create database engine
    engine = create_async_engine(settings.POSTGRES_URL, echo=True)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if admin already exists
        from sqlalchemy import select
        result = await session.execute(
            select(AdminUserModel).where(AdminUserModel.email == "admin@elles.com")
        )
        existing = result.scalar_one_or_none()

        if existing:
            print("Admin user already exists!")
            return

        # Hash password
        password_hasher = BcryptPasswordHasherAdapter()
        hashed_password = await password_hasher.hash_password("Admin123!")

        # Create admin user
        admin = AdminUserModel(
            id=uuid4(),
            email="admin@elles.com",
            password_hash=hashed_password,
            full_name="System Administrator",
            role="ADMIN",
            is_active=True
        )

        session.add(admin)
        await session.commit()

        print("✅ Initial admin user created!")
        print("   Email: admin@elles.com")
        print("   Password: Admin123!")
        print("   ⚠️  Change this password immediately in production!")


if __name__ == "__main__":
    asyncio.run(create_initial_admin())