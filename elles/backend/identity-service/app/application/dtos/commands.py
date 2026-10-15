import uuid

from pydantic import BaseModel, EmailStr, Field

class LoginAdminCommand(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    correlation_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Tracing ID from HTTP request"
    )
    