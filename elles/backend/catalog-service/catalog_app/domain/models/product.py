from dataclasses import dataclass , field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from catalog_app.domain.exceptions import DomainException, InvalidPriceError
class ProductStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

@dataclass
class Price:
    amount: int
    currency: str ="Ksh"

    def __post_init__(self):
        if self.amount <= 0:
            raise InvalidPriceError("Price cannot be less than zero")

@dataclass
class Size:
    value: float
    unit: str = "ml"
@dataclass
class Variant:
    sku: str
    price: Price
    shade_name: Optional[str] = None
    size: Optional[Size] = None
    images: List[str] = field(default_factory=list)
    is_active: bool = True

@dataclass
class Product:
    created_by: UUID
    id: UUID = field(default_factory=uuid4)
    slug: str = ""
    name: str = ""
    brand: str =""
    category: str =""
    description: str = ""
    benefits: List[str] = field(default_factory=list)
    how_to_use: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    variants: List[Variant] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    status: str = "draft"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

    def publish(self) -> None:
        if not self.name or not self.slug:
            raise DomainException("Product must have a name, a slug, and atleast one active variant")
        if not any(v.is_active for v in self.variants):
            raise DomainException("Product must have an active variant")

        self.status = "published"
        self.updated_at = datetime.now(timezone.utc)

    def archive(self) -> None:
        self.status = ProductStatus.ARCHIVED.value
        self.updated_at = datetime.now(timezone.utc)

    def add_variant(self, variant: Variant) -> None:
        if any(v.sku == variant.sku for v in self.variants):
            raise DomainException(f"Duplicate SKU: {variant.sku}")

        self.variants.append(variant)
        self.updated_at = datetime.now(timezone.utc)






