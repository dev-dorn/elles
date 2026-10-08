from typing import Protocol, Optional
from uuid import UUID
from app.domain.models.product import Product

class ProductRepositoryPort(Protocol):
    async def save(self,product: Product) -> None: ...
    async def get_by_id(self, product_id: UUID) ->  Optional[Product]: ...
    