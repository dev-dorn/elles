# catalog_app/presentation/api/security.py
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from catalog_app.infrastructure.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AdminPrincipal:
    user_id: UUID
    role: str


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _decode_admin(token: str) -> AdminPrincipal:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],  # never trust the token's own "alg"
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Token has expired")
    except jwt.InvalidTokenError:
        raise _unauthorized("Invalid token")

    try:
        user_id = UUID(str(payload["sub"]))
    except ValueError:
        raise _unauthorized("Invalid token subject")

    claim = payload.get("role") or payload.get("roles") or []
    roles = {claim} if isinstance(claim, str) else set(claim)
    if settings.ADMIN_ROLE.lower() not in {str(r).lower() for r in roles}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    return AdminPrincipal(user_id=user_id, role=settings.ADMIN_ROLE)


async def require_admin(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> AdminPrincipal:
    if creds is None:
        raise _unauthorized("Not authenticated")
    return _decode_admin(creds.credentials)


async def optional_admin(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[AdminPrincipal]:
    """Returns the admin if a valid admin token is present, otherwise None."""
    if creds is None:
        return None
    try:
        return _decode_admin(creds.credentials)
    except HTTPException:
        return None