from datetime import datetime, timedelta, timezone
from uuid import UUID
from jose import jwt , JWTError
from identity_app.application.ports.jwt_service import JWTServicePort
from identity_app.infrastructure.config import settings

class JWTServiceAdapter(JWTServicePort):
    """
    implements JWTServicePort interface token generation using python-jose    """
    def __init__(self):
        self._secret_key = settings.JWT_SECRET_KEY
        self._algorithm = settings.JWT_ALGORITHM

    async def create_access_token(self, user_id: UUID, email: str, role:str)-> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        payload = {
            "sub": str(user_id),
            "email": email,
            "role":role,
            "exp": expire,
            "type": "access"

        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
    async def create_refresh_token(self,
                                   user_id: UUID
                                   ) ->str:
        expire = datetime.now(timezone.utc) + timedelta(days=7)
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "type": "refresh"
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
    async def decode_token(self,
                           token: str
                           ) -> dict:
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            return payload
        except JWTError:
            raise ValueError("Invalid token")

