from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from catalog_app.domain.models.product import Product

Category = Literal["makeup", "fragrance", "skincare", "haircare", "bodycare", "nails", "tools"]


class PriceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    amount: int
    currency: str


class SizeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    value: float
    unit: str


class VariantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


    sku: str
    shade_name: Optional[str] = None
    size: Optional[SizeResponse] = None
    price: PriceResponse
    images: List[str] = []
    is_active: bool = True


class ProductResponse(BaseModel):
    """Full product, used by create and get-by-slug."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    brand: str
    category: str
    description: str
    benefits: List[str]
    how_to_use: List[str]
    attributes: Dict[str, Any]
    variants: List[VariantResponse]
    images: List[str]
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class ProductSummary(BaseModel):
    """Lightweight card for list pages."""
    id: UUID
    slug: str
    name: str
    brand: str
    category: str
    status: str
    image: Optional[str] = None
    price_from: Optional[PriceResponse] = None
    variant_count: int

    @classmethod
    def from_domain(cls, p: Product) -> "ProductSummary":
        active = [v for v in p.variants if v.is_active]
        cheapest = min(active, key=lambda v: v.price.amount) if active else None
        return cls(
            id=p.id,
            slug=p.slug,
            name=p.name,
            brand=p.brand,
            category=p.category,
            status=p.status,
            image=p.images[0] if p.images else None,
            price_from=PriceResponse(amount=cheapest.price.amount, currency=cheapest.price.currency)
            if cheapest else None,
            variant_count=len(active),
        )


class ProductListResponse(BaseModel):
    items: List[ProductSummary]
    total: int
    page: int
    page_size: int
    pages: int