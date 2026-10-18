# scripts/create_admin.py
import asyncio
import sys
import os

# Robust path appending: works no matter which directory you run the script from
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from identity_app.infrastructure.persistence.postgres.models import Base, AdminUserModel
from identity_app.infrastructure.security.password_hasher import BcryptPasswordHasherAdapter
from identity_app.infrastructure.config import settings
from uuid import uuid4

async def create_initial_admin():
    """Creates or reactivates the initial admin user in the database."""

    # Create database engine (set echo=False to reduce terminal noise, or True to see SQL)
    engine = create_async_engine(settings.POSTGRES_URL, echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if admin already exists
        result = await session.execute(
            select(AdminUserModel).where(AdminUserModel.email == "admin@elles.com")
        )
        existing = result.scalar_one_or_none()

        password_hasher = BcryptPasswordHasherAdapter()
        hashed_password = await password_hasher.hash_password("Admin123!")

        if existing:
            if not existing.is_active:
                # FIX: Reactivate the user if they were soft-deleted
                print("⚠️ Admin user exists but is INACTIVE. Reactivating...")
                existing.is_active = True
                existing.password_hash = hashed_password  # Reset password just in case
                existing.full_name = "System Administrator"
                await session.commit()
                print("✅ Admin user REACTIVATED successfully!")
                print(f"   Admin ID: {existing.id}")
            else:
                print("ℹ️ Admin user already exists and is ACTIVE!")
                print(f"   Admin ID: {existing.id}")
            return

        # Create admin user (Fixed the 'adminn' typo here)
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
        print(f"   Admin ID: {admin.id}")
        print("   Email: admin@elles.com")
        print("   Password: Admin123!")

if __name__ == "__main__":
    asyncio.run(create_initial_admin())