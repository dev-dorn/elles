from typing import Optional

from catalog_app.application.ports.repositories import ProductRepositoryPort
from catalog_app.domain.models.product import Product


class PublishProductUseCase:
    def __init__(self, product_repo: ProductRepositoryPort):
        self._product_repo = product_repo

    async  def execute(self, slug: str) -> Optional[Product]:
        product = await self._product_repo.get_by_slug(slug)
        if product is None:
            return None

        product.publish()
        await self._product_repo.save(product)
        return product

class ArchiveProductUseCase:
    def __init__(self, product_repo: ProductRepositoryPort):
        self._product_repo = product_repo

    async def execute(self, slug: str) -> Optional[Product]:
        product = await self._product_repo.get_by_slug(slug)
        if product is None:
            return None
        product.archive()
        await self._product_repo.save(product)
        return product