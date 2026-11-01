"""An in-memory repository that follows the same contract as MongoProductRepository."""
from copy import deepcopy
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from catalog_app.application.ports.repositories import ProductFilters, ProductRepositoryPort
from catalog_app.domain.exceptions import DuplicateProductError
from catalog_app.domain.models.product import Product


def _matches(p: Product, f: ProductFilters) -> bool:
    if f.category and p.category != f.category:
        return False
    if f.brand and p.brand != f.brand:
        return False
    if f.status and p.status != f.status:
        return False
    if f.q and f.q.lower() not in p.name.lower():
        return False

    prices = [v.price.amount for v in p.variants]
    # Mongo applies $gte and $lte to an array field independently, so each bound is checked on its own.
    if f.min_price is not None and not any(a >= f.min_price for a in prices):
        return False
    if f.max_price is not None and not any(a <= f.max_price for a in prices):
        return False

    if f.scent_family and f.scent_family not in p.attributes.get("scent_family", []):
        return False
    if f.skin_type and f.skin_type not in p.attributes.get("skin_types", []):
        return False
    return True


class FakeProductRepository(ProductRepositoryPort):
    def __init__(self) -> None:
        self.items: Dict[UUID, Product] = {}

    def add(self, product: Product) -> None:
        """Seed a product directly, bypassing the use cases."""
        self.items[product.id] = deepcopy(product)

    async def save(self, product: Product) -> None:
        skus = {v.sku for v in product.variants}
        for other in self.items.values():
            if other.id == product.id:
                continue
            if other.slug == product.slug:
                raise DuplicateProductError(f"A product with slug '{product.slug}' already exists.")
            if skus & {v.sku for v in other.variants}:
                raise DuplicateProductError("One or more SKUs already exist on another product.")
        self.items[product.id] = deepcopy(product)

    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
        found = self.items.get(product_id)
        return deepcopy(found) if found else None

    async def get_by_slug(self, slug: str) -> Optional[Product]:
        for p in self.items.values():
            if p.slug == slug:
                return deepcopy(p)
        return None

    async def search(
        self, filters: ProductFilters, page: int, page_size: int
    ) -> Tuple[List[Product], int]:
        matched = [p for p in self.items.values() if _matches(p, filters)]
        matched.sort(key=lambda p: p.created_at, reverse=True)
        start = (page - 1) * page_size
        return [deepcopy(p) for p in matched[start:start + page_size]], len(matched)
