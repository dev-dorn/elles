from uuid import UUID

from app.application.dtos.admin_dtos import UpdateAdminProfileRequest
from app.domain.exceptions import DomainException
from app.domain.models.admin_user import AdminUser
from app.infrastructure.security.jwt_service import JWTServiceAdapter


class UpdateAdminProfileUseCase:
    def __init__(self, security_service: JWTServiceAdapter, user_repo=None):
        self._user_repo = user_repo

    async def execute(self, user_id: UUID, request: UpdateAdminProfileRequest) -> AdminUser:
        user = await self._user_repo.get_by_id(user_id)

        if not user:
            raise DomainException("Admin user not found")

        user.full_name = request.full_name

        await self._user_repo.save(user)

        return  user
