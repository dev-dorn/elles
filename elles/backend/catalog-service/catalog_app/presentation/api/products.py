
from fastapi import APIRouter, Depends, HTTPException, status, Header
from uuid import UUID
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from catalog_app.application.dtos.product_dtos import CreateProductRequest
from catalog_app.application.use_cases.create_product import CreateProductUseCase
from catalog_app.domain.exceptions import InvalidPriceError, DomainException
from catalog_app.infrastructure.persistence.mongodb.database import get_mongodb_session
from catalog_app.infrastructure.persistence.mongodb.product_repository import MongoProductRepository

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_product(
        request: CreateProductRequest,
        db: AsyncIOMotorDatabase = Depends(get_mongodb_session),

        x_admin_id: Optional[UUID] = Header(None, alias="X-Admin-Id")
):
    if not x_admin_id:
        x_admin_id = UUID("c86af85a-f58d-4235-b4ad-f2153eb15e69")

    product_repo = MongoProductRepository(db=db)

    use_case = CreateProductUseCase(product_repo=product_repo)

    try:
        new_product = await use_case.execute(request, created_by=x_admin_id)

        return {
            "message": "Product draft created successfully",
            "product_id": str(new_product.id),
            "status": new_product.status,
            "name": new_product.name

        }
    except InvalidPriceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
