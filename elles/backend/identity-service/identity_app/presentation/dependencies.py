from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from identity_app.infrastructure.security.jwt_service import JWTServiceAdapter

security = HTTPBearer()


async def get_current_admin(
        credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    jwt_service = JWTServiceAdapter()

    try:
        payload = await jwt_service.decode_token(credentials.credentials)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource",
        )

    return payload