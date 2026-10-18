from typing import Protocol, Optional
from uuid import UUID
from catalog_app.domain.models.product import Product
from abc import ABC, abstractmethod


class ProductRepositoryPort(ABC):
    @abstractmethod
    async def save(self, product: Product) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
        pass
    @abstractmethod
    async def get_by_slug(self, slug: str) -> Optional[Product]:
        pass