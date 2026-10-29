from uuid import UUID
from catalog_app.application.ports.repositories import ProductRepositoryPort
from catalog_app.application.dtos.product_dtos import CreateProductRequest
from catalog_app.domain.exceptions import  DuplicateProductError
from catalog_app.domain.models.product import Product, Variant, Price, Size


class CreateProductUseCase:
    def __init__(self, product_repo: ProductRepositoryPort):
        self._product_repo = product_repo

    async def execute(self, request: CreateProductRequest, created_by: UUID) -> Product:
        if await self._product_repo.get_by_slug(request.slug):
            raise DuplicateProductError(f"A product with slug '{request.slug}' already exists.")

        variants = [
            Variant(
                sku=v.sku,
                shade_name=v.shade_name,
                size=Size(value=v.size.value, unit=v.size.unit) if v.size else None,
                price=Price(amount=v.price.amount, currency=v.price.currency),
                images=list(v.images),
                is_active=v.is_active,
            )
            for v in request.variants
        ]

        product = Product(
            slug=request.slug,
            name=request.name,
            brand=request.brand,
            category=request.category,
            description=request.description,
            benefits=list(request.benefits),
            how_to_use=list(request.how_to_use),
            attributes=request.attributes.model_dump(exclude_none=True),
            variants=variants,
            images=list(request.images),
            status=request.status,
            created_by=created_by,
        )

        await self._product_repo.save(product)
        return product