import logging
from app.application.ports.repositories import AdminUserRepositoryPort
from app.application.ports.password_hasher import PasswordHasherPort
from app.application.ports.jwt_service import JWTServicePort
from app.application.dtos.commands import LoginAdminCommand
from app.application.dtos.responses import TokenResponse
from app.domain.exceptions import InvalidCredentialsError, InactiveAccountError

security_logger = logging.getLogger("security.auth")


class LoginAdminUseCase:
    def __init__(
            self,
            user_repo: AdminUserRepositoryPort,
            password_hasher: PasswordHasherPort,
            jwt_service: JWTServicePort
    ):
        self._user_repo = user_repo
        self._password_hasher = password_hasher
        self._jwt_service = jwt_service

    async def execute(self, command: LoginAdminCommand) -> TokenResponse:
        # 1. Fetch user by email
        user = await self._user_repo.get_by_email(command.email)

        if not user:
            security_logger.warning(f"Failed login attempt for unknown email: {command.email}")
            raise InvalidCredentialsError("Invalid email or password")

        # 2. Check if account is active
        if not user.is_active:
            security_logger.warning(f"Login attempt on deactivated account: {user.id}")
            raise InactiveAccountError("Account is deactivated")

        # 3. Verify password
        is_valid = await self._password_hasher.verify_password(command.password, user.password_hash)

        if not is_valid:
            security_logger.warning(f"Failed login attempt (bad password) for user: {user.id}")
            raise InvalidCredentialsError("Invalid email or password")

        # 4. Update last login timestamp
        user.update_last_login()
        await self._user_repo.save(user)

        security_logger.info(f"Successful admin login: {user.id} ({user.email})")

        # 5. Generate JWT tokens (Expiration is handled inside the JWT service)
        access_token = await self._jwt_service.create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value
        )

        refresh_token = await self._jwt_service.create_refresh_token(user_id=user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=900  # 15 minutes
        )