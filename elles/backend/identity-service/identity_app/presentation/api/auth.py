# app/presentation/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from identity_app.infrastructure.persistence.postgres.database import get_db_session
from identity_app.infrastructure.persistence.postgres.admin_user_repository import PostgresAdminUserRepository
from identity_app.infrastructure.security.password_hasher import BcryptPasswordHasherAdapter
from identity_app.infrastructure.security.jwt_service import JWTServiceAdapter
from identity_app.application.use_cases.login_admin import LoginAdminUseCase
from identity_app.application.dtos.commands import LoginAdminCommand
from identity_app.application.dtos.responses import TokenResponse
from identity_app.domain.exceptions import InvalidCredentialsError, InactiveAccountError

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login_admin(
        command: LoginAdminCommand,
        db: AsyncSession = Depends(get_db_session)
):
    """
    Admin login endpoint.
    Returns JWT access and refresh tokens.
    """
    # Wire up dependencies
    user_repo = PostgresAdminUserRepository(session=db)
    password_hasher = BcryptPasswordHasherAdapter()
    jwt_service = JWTServiceAdapter()

    # Create use case
    use_case = LoginAdminUseCase(
        user_repo=user_repo,
        password_hasher=password_hasher,
        jwt_service=jwt_service
    )

    try:
        # Execute use case
        tokens = await use_case.execute(command)
        return tokens
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InactiveAccountError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )