import logging
from dataclasses import dataclass
from typing import FrozenSet, Optional
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from inventory_app.infrastructure.config import settings

logger = logging.getLogger("inventory-service.auth")

bearer_scheme = HTTPBearer(auto_error=False)

@dataclass(frozen=True)
class Principal:
    """Who is calling: the user (or service) id from the token, and their roles in lower case."""
    user_id: UUID
    roles: FrozenSet[str]

def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )
def _decode(token: str) -> Principal:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],  # never trust the algorithm named in the token itself
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Token has expired")
    except jwt.InvalidTokenError as exc:
        logger.warning("JWT rejected: %s: %s", type(exc).__name__, exc)
        raise _unauthorized("Invalid token")

    try:
        user_id = UUID(str(payload["sub"]))
    except ValueError:
        raise _unauthorized("Invalid token subject")

    claim = payload.get("role") or payload.get("roles") or []
    roles = {claim} if isinstance(claim, str) else set(claim)
    return Principal(user_id=user_id, roles=frozenset(str(r).lower() for r in roles))

async def get_principal(
        creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Principal:
    """Any valid token. 401 when there is none, or it does not verify."""
    if creds is None:
        raise _unauthorized("Not authenticated")
    return _decode(creds.credentials)

def require_roles(*allowed: str):
    """A dependency that lets through only callers holding one of the given roles (403 otherwise)."""
    wanted = {role.lower() for role in allowed}

    async def dependency(principal: Principal = Depends(get_principal)) -> Principal:
        if not (principal.roles & wanted):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return principal

    return dependency
# Stock levels and adjustments: admins only.

require_admin = require_roles(settings.ADMIN_ROLE)
# Reservations: admins, and other services (order-service) acting on an order's behalf.

require_admin_or_service = require_roles(settings.ADMIN_ROLE, settings.SERVICE_ROLE)
