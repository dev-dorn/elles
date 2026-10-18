# app/application/use_cases/update_admin_profile.py
from uuid import UUID
from identity_app.application.ports.repositories import AdminUserRepositoryPort
from identity_app.domain.models.admin_user import AdminUser
from identity_app.domain.exceptions import DomainException
from identity_app.application.dtos.admin_dtos import UpdateAdminProfileRequest


class UpdateAdminProfileUseCase:
    def __init__(self, user_repo: AdminUserRepositoryPort):
        self._user_repo = user_repo

    async def execute(self, user_id: UUID, request: UpdateAdminProfileRequest) -> AdminUser:
        # 1. Fetch the user
        user = await self._user_repo.get_by_id(user_id)

        if not user:
            raise DomainException("Admin user not found.")

        # 2. Apply changes
        user.full_name = request.full_name

        # 3. Persist changes
        await self._user_repo.save(user)

        return user