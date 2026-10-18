# Catalog Service: Create Product

Documents the product creation flow in `catalog-service`: the endpoint, request schema, validation rules, domain rules, storage and configuration.

## Overview

The catalog models a **product with variants**. A product holds the shared information (name, brand, benefits, how to use). Each variant is a purchasable item with its own SKU, price and images. A variant is a shade (makeup, nails) or a size (fragrance, skincare, haircare, bodycare), or neither (tools).

Stock is **not** stored in the catalog. Quantities belong to `inventory-service` and are joined on `sku`.

## Endpoint

| | |
|---|---|
| Method | `POST` |
| Path | `/api/v1/products/` |
| Body | `CreateProductRequest` (JSON) |
| Success | `201 Created` |
| Duplicate slug or SKU | Domain error (map to `409 Conflict` in the API layer) |
| Invalid body | `422 Unprocessable Entity` |

`created_by` is never accepted from the client. It is taken from the authenticated admin (the JWT `sub` claim) and passed to the use case.

## Request schema

### `CreateProductRequest`

| Field | Type | Rules |
|---|---|---|
| `slug` | string | 3 to 200 chars, lowercase letters, digits and hyphens only (`my-product`). Unique. |
| `name` | string | 3 to 200 chars |
| `brand` | string | 2 to 100 chars |
| `category` | enum | `makeup`, `fragrance`, `skincare`, `haircare`, `bodycare`, `nails`, `tools` |
| `description` | string | 10 to 5000 chars |
| `benefits` | string[] | Optional. Short selling points, for example `"Long-wearing"` |
| `how_to_use` | string[] | Optional. One entry per step |
| `attributes` | object | Optional. Category-specific data (finish, scent notes, skin types) |
| `variants` | `VariantDTO[]` | Required, at least one. SKUs must be unique within the request |
| `images` | string[] | Optional. Product-level image URLs |
| `status` | `"draft"` | Only `draft` is accepted on create. Publishing goes through the domain `publish()` rule |

### `VariantDTO`

| Field | Type | Rules |
|---|---|---|
| `sku` | string | 1 to 64 chars. Unique across all products |
| `price` | `PriceDTO` | Required |
| `shade_name` | string | Optional |
| `size` | `SizeDTO` | Optional |
| `images` | string[] | Optional |
| `is_active` | bool | Default `true` |

### `PriceDTO`

| Field | Type | Rules |
|---|---|---|
| `amount` | integer | Greater than 0. **Minor units**: `18500` = KES 185.00 |
| `currency` | string | 3-letter ISO code, uppercased. Default `KES` |

### `SizeDTO`

| Field | Type | Rules |
|---|---|---|
| `value` | number | Greater than 0 |
| `unit` | string | Default `ml` |

All request models strip whitespace and **reject unknown fields**, so a typo such as `how_too_use` returns a 422 instead of being ignored.

## Example request

```json
{
  "slug": "velvet-matte-lipstick",
  "name": "Velvet Matte Lipstick",
  "brand": "Elles",
  "category": "makeup",
  "description": "A creamy, long-wearing matte lipstick.",
  "benefits": ["Long-wearing", "Non-drying"],
  "how_to_use": ["Apply from the center of the lips outward."],
  "attributes": { "finish": "matte" },
  "variants": [
    {
      "sku": "ELL-LIP-RUBY",
      "shade_name": "Ruby",
      "price": { "amount": 185000, "currency": "KES" },
      "images": [],
      "is_active": true
    }
  ],
  "images": [],
  "status": "draft"
}
```

```bash
curl -X POST http://localhost:8005/api/v1/products/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d @product.json
```

## Architecture

```
presentation/api/products.py          Router, request validation, error mapping
application/dtos/product_dtos.py      Pydantic request models
application/use_cases/create_product.py   CreateProductUseCase
application/ports/repositories.py     ProductRepositoryPort (save, get_by_id, get_by_slug)
domain/models/product.py              Product, Variant, Price, Size
infrastructure/persistence/mongodb/   MongoProductRepository, database client
infrastructure/config.py              Settings
```

Flow: router validates the body into `CreateProductRequest`, calls `CreateProductUseCase.execute(request, created_by)`, which checks the slug is free, maps DTOs to the domain `Product`, and saves it through the repository port.

## Domain rules

- `Price.amount` must be greater than 0.
- `Product.publish()` requires a name, a slug and at least one active variant.
- SKUs must be unique within a product (`Product.add_variant`).
- `created_by` is required and has no default.

## Storage (MongoDB)

- Database `catalog_db`, collection `products`.
- `_id` and `created_by` are stored as string UUIDs.
- Prices are stored as integers in minor units.
- Datetimes are timezone-aware (the client is created with `tz_aware=True`).

Indexes, created at startup by `ensure_indexes()`:

| Index | Purpose |
|---|---|
| `slug` (unique) | Storefront URLs, duplicate slug protection |
| `variants.sku` (unique) | SKUs key inventory and orders |
| `category`, `status` | Listing and filtering |

The use case checks the slug before saving, but two simultaneous requests could both pass that check. The unique indexes are the real guarantee. The repository catches `DuplicateKeyError` and re-raises it as a domain exception.

## Configuration

| Variable | Description | Default |
|---|---|---|
| `ENVIRONMENT` | Runtime environment | `local` |
| `MONGO_URL` | MongoDB connection string | `mongodb://admin:admin@localhost:27017/?authSource=admin` |
| `MONGODB_DB_NAME` | Database name | `catalog_db` |

Settings are case-sensitive, so the variable must be named exactly `MONGO_URL`. In Docker Compose the host is `mongodb`, not `localhost`:

```
MONGO_URL=mongodb://admin:<password>@mongodb:27017/?authSource=admin
```

## Running and verifying

Locally:

```bash
cd backend/catalog-service
uvicorn catalog_app.main:app --host 0.0.0.0 --port 8005 --reload
```

Open `http://localhost:8005/docs`, post the example, then change `slug` and `sku` and post again for a second product. Posting the same slug twice should fail with a duplicate error.

To inspect the data, connect MongoDB Compass to `mongodb://admin:<password>@localhost:27017/?authSource=admin` and open `catalog_db` then `products`. Prices are at `variants[0].price.amount`.

## Known gaps

- Response DTO: the endpoint returns an ad-hoc dict; a `ProductResponse` model is still to be added.
- List and filter endpoint (by category, paginated) is not built yet.
- Update, publish and archive endpoints are not built yet.
- Map the duplicate-slug domain exception to `409` in a global exception handler.
