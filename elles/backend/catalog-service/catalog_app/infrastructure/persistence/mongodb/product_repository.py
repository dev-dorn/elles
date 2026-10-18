from typing import Any, Dict, Optional
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from catalog_app.application.ports.repositories import ProductRepositoryPort
from catalog_app.domain.exceptions import DomainException
from catalog_app.domain.models.product import Product, Size, Variant, Price


def _to_document(p: Product) -> Dict[str, Any]:
    return {
        "id": str(p.id),
        "slug": p.slug,
        "name": p.name,
        "brand": p.brand,
        "category": p.category,
        "description": p.description,
        "benefits": p.benefits,
        "how_to_use": p.how_to_use,
        "attributes": p.attributes,
        "variants": [
            {
                "sku": v.sku,
                "shade_name": v.shade_name,
                "size": {"value": v.size.value, "unit": v.size.unit} if v.size else None,
                "price": {"amount": v.price.amount, "currency": v.price.currency},
                "images": v.images,
                "is_active": v.is_active,


            }
            for v in p.variants


        ],
        "images": p.images,
        "status": p.status,
        "created_by": str(p.created_by),
        "created_at": p.created_at,
        "updated_at": p.updated_at,
    }

def _to_domain(doc: Dict[str, Any]) -> Product:
    variants = [
        Variant(
            sku=v["sku"],
            shade_name=v.get("shade_name"),
            size=Size(value=v["size"]["value"], unit=v["size"]["unit"]) if v.get("size") else None,
            price=Price(amount=int(v["price"]["amount"]), currency=v["price"]["currency"]),
            images=v.get("images", []),
            is_active=v.get("images", True),


        )
        for v in doc.get("variants", [])
    ]
    return Product(
        id=UUID(doc["id"]),
        slug=doc["slug"],
        name=doc["name"],
        brand=doc["brand"],
        category=doc["category"],
        description=doc["description"],
        benefits=doc.get("benefits", []),
        how_to_use=doc.get("how_to_use", []),
        attributes=doc.get("attributes", {}),
        variants=variants,
        images=doc.get("images", []),
        status=doc["status"],
        created_by=UUID(doc["created_by"]),
        created_at=doc["created_at"],
        updated_at=doc.get("updated_at"),


    )
class MongoProductRepository(ProductRepositoryPort):
    def __init__(self, db: AsyncIOMotorDatabase) :
        self._collection = db["products"]

    async def ensure_indexes(self) -> None:
        await self._collection.create_index("slug", unique=True)
        await self._collection.create_index("variants.sku", unique=True)
        await self._collection.create_index([("category", 1), ("status", 1)])

    async def save(self, product: Product) -> None:
        try:
            await self._collection.replace_one(
                {"_id": str(product.id)}, _to_document(product), upsert=True

            )
        except DuplicateKeyError as e:
            key = (e.details or {}).get("keyPattern", {})
            if "slug" in key:
                raise DomainException(f"A product with slug '{product.slug}' already exists.")
            if "variants.sku" in key:
                raise DomainException("One or more SKUs already exist on another product.")
            raise DomainException("Duplicate product data")

    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
        doc = await self._collection.find_one(
            {
                "_id": str(product_id),
            }
        )
        if doc is None:
            return None
        return _to_domain(doc)

    async def get_by_slug(self, slug: str) -> Optional[Product]:
        doc = await self._collection.find_one({"slug": slug})
        if doc is None:
            return None
        return _to_domain(doc) if doc else None




