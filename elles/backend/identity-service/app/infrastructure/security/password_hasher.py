# app/infrastructure/security/password_hasher.py
import asyncio
import bcrypt
from app.application.ports.password_hasher import PasswordHasherPort

class BcryptPasswordHasherAdapter(PasswordHasherPort):
    """
    Infrastructure Adapter: Implements password hashing using native bcrypt.
    PERFORMANCE: Uses asyncio.to_thread to prevent blocking the async event loop.
    """

    async def hash_password(self, plain_password: str) -> str:
        # bcrypt requires bytes. 12 rounds is the modern security standard.
        hashed_bytes = await asyncio.to_thread(
            bcrypt.hashpw,
            plain_password.encode('utf-8'),
            bcrypt.gensalt(rounds=12)
        )
        return hashed_bytes.decode('utf-8')

    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        is_valid = await asyncio.to_thread(
            bcrypt.checkpw,
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
        return is_valid