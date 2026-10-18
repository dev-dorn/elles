from pydantic import BaseModel, Field
from uuid import UUID

class PublishProductCommand(BaseModel):
    product_id = UUID
    correlation_id: str = Field(..., description="Tracing ID from the HTTP request")