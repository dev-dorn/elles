from datetime import datetime
from typing import Annotated, List, Literal, Optional
from uuid import UUID


from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Sku = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]

class _Base(BaseModel):
    model_config =  ConfigDict(str_strip_whitespace=True, extra="forbid")

class AdjustStockRequest(_Base):
    delta: int = Field(..., ge=-1_000_000)