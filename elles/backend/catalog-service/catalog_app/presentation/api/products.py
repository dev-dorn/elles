# catalog_app/presentation/api/products.py
import math
from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from catalog_app.application.dtos.product_dtos import CreateProductRequest
from catalog_app.application.dtos.product_responses import (
    Category,
    ProductListResponse,
    ProductResponse,
    ProductSummary,
)
from catalog_app.application.ports.repositories import ProductFilters, ProductRepositoryPort
from catalog_app.application.use_cases.create_product import CreateProductUseCase
from catalog_app.application.use_cases.product_queries import ListProductsUseCase, GetProductBySlugUseCase

from catalog_app.domain.exceptions import DomainException, InvalidPriceError
from catalog_app.infrastructure.persistence.mongodb.database import get_mongodb_session
from catalog_app.infrastructure.persistence.mongodb.product_repository import MongoProductRepository

router = APIRouter(prefix="/products", tags=["Products"])


def get_product_repo(db: AsyncIOMotorDatabase = Depends(get_mongodb_session)) -> ProductRepositoryPort:
    return MongoProductRepository(db=db)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_product(
    request: CreateProductRequest,
    repo: ProductRepositoryPort = Depends(get_product_repo),
    x_admin_id: Optional[UUID] = Header(None, alias="X-Admin-Id"),
):
    if not x_admin_id:
        x_admin_id = UUID("c86af85a-f58d-4235-b4ad-f2153eb15e69")

    use_case = CreateProductUseCase(product_repo=repo)

    try:
        new_product = await use_case.execute(request, created_by=x_admin_id)
        return {
            "message": "Product draft created successfully",
            "product_id": str(new_product.id),
            "status": new_product.status,
            "name": new_product.name,
        }
    except InvalidPriceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=ProductListResponse)
async def list_products(
    category: Optional[Category] = None,
    brand: Optional[str] = None,
    status_filter: Literal["draft", "published", "archived"] = Query("published", alias="status"),
    q: Optional[str] = Query(None, min_length=2, max_length=100, description="Name search"),
    min_price: Optional[int] = Query(None, ge=0, description="Minor units"),
    max_price: Optional[int] = Query(None, ge=0, description="Minor units"),
    scent_family: Optional[str] = None,
    skin_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repo: ProductRepositoryPort = Depends(get_product_repo),
):
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="min_price cannot be greater than max_price",
        )

    filters = ProductFilters(
        category=category,
        brand=brand,
        status=status_filter,
        q=q,
        min_price=min_price,
        max_price=max_price,
        scent_family=scent_family,
        skin_type=skin_type,
    )
    products, total = await ListProductsUseCase(repo).execute(filters, page, page_size)
    return ProductListResponse(
        items=[ProductSummary.from_domain(p) for p in products],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/{slug}", response_model=ProductResponse)
async def get_product(slug: str, repo: ProductRepositoryPort = Depends(get_product_repo)):
    product = await GetProductBySlugUseCase(repo).execute(slug)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return ProductResponse.model_validate(product)