"""Shared builders for the catalog tests: tokens, request payloads and domain products."""
import time
from datetime import datetime
from typing import Any, Dict, Optional, Sequence
from uuid import UUID

import jwt

from catalog_app.domain.models.product import Price, Product, Variant
from catalog_app.infrastructure.config import settings

ADMIN_ID = UUID("c86af85a-f58d-4235-b4ad-f2153eb15e69")


def make_token(
    *,
    sub: Optional[str] = None,
    role: Optional[str] = "ADMIN",
    expires_in: int = 3600,
    secret: Optional[str] = None,
    include_exp: bool = True,
) -> str:
    """Build a JWT shaped like the ones identity-service issues."""
    payload: Dict[str, Any] = {"sub": str(ADMIN_ID) if sub is None else sub}
    if role is not None:
        payload["role"] = role
    if include_exp:
        payload["exp"] = int(time.time()) + expires_in
    return jwt.encode(payload, secret or settings.JWT_SECRET_KEY, algorithm="HS256")


def auth(token: Optional[str] = None) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token or make_token()}"}


def makeup_payload(**overrides: Any) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "slug": "velvet-matte-lipstick",
        "name": "Velvet Matte Lipstick",
        "brand": "Elles",
        "category": "makeup",
        "description": "A creamy, long-wearing matte lipstick.",
        "benefits": ["Long-wearing"],
        "how_to_use": ["Apply from the center of the lips outward."],
        "attributes": {"finish": "matte"},
        "variants": [
            {"sku": "ELL-LIP-RUBY", "shade_name": "Ruby", "price": {"amount": 185000, "currency": "KES"}}
        ],
        "images": [],
        "status": "draft",
    }
    payload.update(overrides)
    return payload


def fragrance_payload(**overrides: Any) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "slug": "golden-hour-eau-de-parfum",
        "name": "Golden Hour Eau de Parfum",
        "brand": "Elles",
        "category": "fragrance",
        "description": "A warm, sunlit fragrance with citrus, jasmine and soft amber.",
        "attributes": {
            "concentration": "eau-de-parfum",
            "gender_target": "women",
            "scent_family": ["floral", "warm"],
            "notes": {"top": ["bergamot"], "heart": ["jasmine"], "base": ["amber", "musk"]},
        },
        "variants": [
            {"sku": "ELL-FRG-GH-50", "size": {"value": 50, "unit": "ml"}, "price": {"amount": 850000}},
            {"sku": "ELL-FRG-GH-100", "size": {"value": 100, "unit": "ml"}, "price": {"amount": 1350000}},
        ],
        "status": "draft",
    }
    payload.update(overrides)
    return payload


def make_product(
    slug: str,
    *,
    category: str = "makeup",
    status: str = "published",
    brand: str = "Elles",
    amounts: Sequence[int] = (10000,),
    active: Optional[Sequence[bool]] = None,
    attributes: Optional[Dict[str, Any]] = None,
    created_at: Optional[datetime] = None,
) -> Product:
    """A domain product with one variant per amount. SKUs are derived from the slug, so they are unique."""
    flags = list(active) if active is not None else [True] * len(amounts)
    variants = [
        Variant(sku=f"{slug}-{i}".upper(), price=Price(amount=amount), is_active=flag)
        for i, (amount, flag) in enumerate(zip(amounts, flags))
    ]
    extra: Dict[str, Any] = {"created_at": created_at} if created_at else {}
    return Product(
        created_by=ADMIN_ID,
        slug=slug,
        name=slug.replace("-", " ").title(),
        brand=brand,
        category=category,
        description="A test product description.",
        attributes=attributes or {},
        variants=variants,
        status=status,
        **extra,
    )
