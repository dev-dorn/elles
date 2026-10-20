# catalog_app/application/use_cases/product_queries.py
from typing import List, Optional, Tuple

from catalog_app.application.ports.repositories import ProductFilters, ProductRepositoryPort
from catalog_app.domain.models.product import Product


class ListProductsUseCase:
    def __init__(self, product_repo: ProductRepositoryPort):
        self._product_repo = product_repo

    async def execute(
        self, filters: ProductFilters, page: int, page_size: int
    ) -> Tuple[List[Product], int]:
        return await self._product_repo.search(filters, page, page_size)


class GetProductBySlugUseCase:
    def __init__(self, product_repo: ProductRepositoryPort):
        self._product_repo = product_repo

    async def execute(self, slug: str) -> Optional[Product]:
        return await self._product_repo.get_by_slug(slug)