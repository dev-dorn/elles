import re
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class _Base(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

class PriceDTO(_Base):
    amount: int = Field(..., gt=0, description="Smallest currency unit (18500 = KES 185.00)")
    currency: str = Field(default="KES", min_length=3, max_length=3)

    @field_validator("currency")
    @classmethod
    def currency_upper(cls, v: str) -> str:
        v=v.upper()
        if not v.isalpha():
            raise ValueError("Currency must be a 3-letter ISO code, e.g. 'KES'")
        return v

class SizeDTO(_Base):
        value: float = Field(..., gt=0)
        unit : str = Field(default="ml", min_length=1)

class VariantDTO(_Base):
        sku: str = Field(..., min_length=1, max_length=64)
        price: PriceDTO
        shade_name: Optional[str] = None
        size: Optional[SizeDTO] = None
        images: List[str]= Field(default_factory=list)
        is_active: bool = True
class CreateProductRequest(_Base):
    slug: str = Field(..., min_length=3, max_length=200)
    name: str = Field(..., min_length=3, max_length=200)
    brand: str = Field(..., min_length=3, max_length=200)
    category: Literal["makeup", "fragrance", "skincare", "haircare", "bodycare", "nails", "tools"]
    description: str= Field(..., min_length=10, max_length=5000)
    benefits: List[str] = Field(default_factory=list)
    how_to_use: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    variants: List[VariantDTO] = Field(..., min_length=1)
    images: List[str] = Field(default_factory=list)
    status: Literal["draft"]= "draft"

    @field_validator("slug")
    @classmethod
    def slug_must_be_url_safe(cls, v: str)-> str:
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", v):
            raise ValueError("Slug must be lowercase, alphanumeric, hyphen-separated (e.g. 'my-product')")
        return v

    @model_validator(mode="after")
    def unique_skus(self):
        skus = [v.sku for v in self.variants]
        dupes = {s for s in skus if skus.count(s) > 1}
        if dupes:
            raise ValueError(f"Duplicate SKUs in request: {sorted(dupes)}")
        return self






