from uuid import UUID
from identity_app.application.ports.repositories import AdminUserRepositoryPort
from identity_app.domain.exceptions import DomainException

class DeactivateAdminUseCase:
    def __init__(self, user_repo: AdminUserRepositoryPort):
        self._user_repo = user_repo

    async def execute(self, user_id: UUID)-> None:
        user = await self._user_repo.get_by_id(user_id)

        if not user:
            raise DomainException("Admin user not found")

        user.deactivate()

        await self._user_repo.save(user)