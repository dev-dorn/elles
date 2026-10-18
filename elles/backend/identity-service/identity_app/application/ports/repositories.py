from typing import Optional, Protocol
from uuid import UUID

from identity_app.domain.models.admin_user import AdminUser


class AdminUserRepositoryPort(Protocol):
    async def save(self, user: AdminUser) -> None: ...

    async def get_by_id(self, user_id: UUID) -> Optional[AdminUser]: ...
    async def get_by_email(self, email: str) -> Optional[AdminUser]: ...
    
