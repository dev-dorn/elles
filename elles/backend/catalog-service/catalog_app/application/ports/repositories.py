from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Tuple
from uuid import UUID

from catalog_app.domain.models.product import Product


@dataclass
class ProductFilters:
    category: Optional[str] = None
    brand: Optional[str] = None
    status: Optional[str] = "published"
    q: Optional[str] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    scent_family: Optional[str] = None
    skin_type: Optional[str] = None


class ProductRepositoryPort(ABC):
    @abstractmethod
    async def save(self, product: Product) -> None:
        """Insert or update. Raises DomainException on duplicate slu or SKU"""

    @abstractmethod
    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
        ...
    @abstractmethod
    async def get_by_slug(self, slug: str) -> Optional[Product]:
        ...
    @abstractmethod
    async def search(
            self, filters: ProductFilters, page: int, page_size: int

    ) -> Tuple[List[Product], int]:
        """Returns (items for this page, total matching """
