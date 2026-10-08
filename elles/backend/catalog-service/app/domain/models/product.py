from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from app.domain.models.product_image import ProductImage
from app.domain.models.value_objects import Price, ProductCategory, ScentProfile , SkincareProfile
from app.domain.events import DomainEvent, ProductPublishedEvent
from app.domain.exceptions import InvalidProductStateError
class ProductStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHES ="PUBLISHED"
    ARCHIVED = "ARCHIVED"

@dataclass
class Product:
    """Aggregate root represents any product"""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    brand: str = ""
    description: str = ""
    category: ProductCategory = ProductCategory.PERFUME
    price : Optional[Price] = None
    scent_profile : Optional[ScentProfile] =None
    skincare_profile: Optional[SkincareProfile] = None
    images: List[ProductImage] = field(default_factory=list)
    status: ProductStatus = ProductStatus.DRAFT
    created_at : datetime = field(default_factory=datetime.utcnow)

_domain_events: List[DomainEvent] = field(default_factory=list, init=False, repr=False)

def add_image(self, image_url:str, alt_text: str, is_primary: bool = False):
    new_image = ProductImage(image_url=image_url, alt_text=alt_text, is_primary=is_primary)
    if is_primary:
        for img in self.images:
            img.is_primary = False

    self.images.append(new_image)


def set_price(self, amount: float, currency: str="USD"):
    from decimal import Decimal
    self.price = Price(amount=Decimal(str(amount)), currency=currency)

    def publish(self, correlation_id: str):
        if self.status != ProductStatus.DRAFT:
            raise InvalidProductStateError(f"Cannot publish product. Current status is {self.status}.")
        
        if not self.price:
            raise InvalidProductStateError("Cannot publish a product without a price.")
            
        if not any(img.is_primary for img in self.images):
            raise InvalidProductStateError("Cannot publish a product without a primary image.")

        if self.category == ProductCategory.PERFUME:
            if not self.scent_profile:
                raise InvalidProductStateError("Perfumes must have a scent profile before publishing.")
        
        elif self.category == ProductCategory.SKINCARE:
            if not self.skincare_profile:
                raise InvalidProductStateError("Skincare products must have a skincare profile before publishing.")

        self.status = ProductStatus.PUBLISHED
        
        self._domain_events.append(
            ProductPublishedEvent.create(
                aggregate_id=self.id, 
                correlation_id=correlation_id,
                name=self.name,
                brand=self.brand,
                category=self.category.value
            )
        )
def pull_domain_events(self) -> List[DomainEvent]:
    events = self._domain_events.copy()
    self._domain_events.clear()
    return events

        





