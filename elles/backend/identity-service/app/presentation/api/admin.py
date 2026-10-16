from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.application.dtos.admin_dtos import UpdateAdminProfileRequest
from app.application.use_cases.update_admin_profile import UpdateAdminProfileUseCase
from app.domain.exceptions import DomainException
from app.infrastructure.persistence.postgres.admin_user_repository import PostgresAdminUserRepository
from app.infrastructure.persistence.postgres.database import get_db_session
from app.presentation.dependencies import get_current_admin
router = APIRouter(prefix="/admin", tags=["Admin Management " ])

@router.put("/")
async def update_my_profile(
        request: UpdateAdminProfileRequest,
        db: AsyncSession = Depends(get_db_session),
        current_admin: dict = Depends(get_current_admin),
):
    user_id = UUID(current_admin["sub"])

    user_repo = PostgresAdminUserRepository(session=db)
    use_case = UpdateAdminProfileUseCase(user_repo =user_repo)

    try:
        updated_admin = await use_case.execute(
            user_id, request)
        return {
            "message": "Profile updated successfully",
            "admin_id": str(updated_admin.id),
            "full_name": updated_admin.full_name,
            "email": updated_admin.email,


        }
    except DomainException as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(err)
        )

