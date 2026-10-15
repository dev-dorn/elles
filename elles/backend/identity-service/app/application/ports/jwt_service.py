from typing import Protocol
from uuid import UUID

class JWTServicePort(Protocol):
    """Port for the JWT service"""
    async def create_access_token(self,
                                  user_id: UUID,
                                  email: str,
                                  role: str
                                  ) ->str: ...
    async def create_refresh_token(self,
                                   user_id: UUID
                                   ) ->str: ...
    async def decode_token(self,
                           token: str
                           ) -> dict: ...
