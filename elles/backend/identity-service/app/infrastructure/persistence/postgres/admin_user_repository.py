from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.application.ports.repositories import AdminUserRepositoryPort
from app.domain.models.admin_user import AdminUser, UserRole
from app.infrastructure.persistence.postgres.models import AdminUserModel

class PostgresAdminUserRepository(AdminUserRepositoryPort):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, user: AdminUser)-> None:
        """Persists or updates Admin user Aggregate"""
        user_query_result = await self._session.execute(
            select(AdminUserModel).where(AdminUserModel.id == user.id)

        )
        existing_user = user_query_result.scalar_one_or_none()
        try:
            if existing_user:
                existing_user.email= user.email
                existing_user.password_hash = user.password_hash
                existing_user.role = user.role
                existing_user.is_active = user.is_active
                existing_user.last_login = user.last_login
            else:
                new_user_record = AdminUserModel(
                    id=user.id,
                    email=user.email,
                    password_hash=user.password_hash,
                    full_name=user.full_name,
                    role=user.role,
                    is_active=user.is_active,
                    created_at=user.created_at,
                    last_login=user.last_login

                )
                self._session.add(new_user_record)
            await self._session.commit()
        except Exception:
            await  self._session.rollback()
            raise
    async def get_by_id(self, user_id: UUID) -> Optional[AdminUser]:
            id_query_result = await self._session.execute(
                select(AdminUserModel).where(AdminUserModel.id == user_id)

            )
            fetched_user_record = id_query_result.scalar_one_or_none()
            return self._model_to_domain(fetched_user_record) if fetched_user_record else None
    async def get_by_email(self, email: str) -> Optional[AdminUser]:
            email_query_result = await self._session.execute(
                select(AdminUserModel).where(AdminUserModel.email == email)

            )
            fetched_user_record = email_query_result.scalar_one_or_none()

            return self ._model_to_domain(fetched_user_record) if fetched_user_record else None

    def _model_to_domain(self,
                         model: AdminUserModel) -> AdminUser:
            return AdminUser(
                id=model.id,
                email=model.email or "",
                password_hash=model.password_hash or "",
                full_name=model.full_name or "",
                role=model.role or UserRole.ADMIN,
                is_active=model.is_active if model.is_active is not None else True,
                created_at=model.created_at or datetime.now(timezone.utc),
                last_login=model.last_login or datetime.now(timezone.utc),


            )




