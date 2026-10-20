# Catalog Service: Products API

Documents the product endpoints in `catalog-service`: create, list, get, publish and archive, with request and response schemas, validation rules, storage and configuration.

## Overview

The catalog models a **product with variants**. A product holds the shared information (name, brand, benefits, how to use). Each variant is a purchasable item with its own SKU, price and images. A variant is a shade (makeup, nails) or a size (fragrance, skincare, haircare, bodycare), or neither (tools).

All categories live in **one `products` collection**. Category-specific data goes in `attributes`, validated per category (see below). Stock is **not** stored in the catalog: quantities belong to `inventory-service` and are joined on `sku`.

## Endpoints

Base path: `/api/v1/products`

| Method | Path | Purpose | Success | Errors |
|---|---|---|---|---|
| `POST` | `/` | Create a product (always starts as `draft`) | `201` | `400` rule violation or duplicate slug/SKU, `422` invalid body |
| `GET` | `/` | List products with filters and pagination | `200` | `422` invalid query |
| `GET` | `/{slug}` | Get one product by slug | `200` | `404` |
| `POST` | `/{slug}/publish` | Move a product to `published` | `200` | `404`, `409` publish rule not met |
| `POST` | `/{slug}/archive` | Move a product to `archived` | `200` | `404` |

### List products: `GET /`

Query parameters:

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `category` | enum | none | `makeup`, `fragrance`, `skincare`, `haircare`, `bodycare`, `nails`, `tools` |
| `brand` | string | none | Exact match |
| `status` | enum | `published` | `draft`, `published` or `archived` |
| `q` | string | none | 2 to 100 chars. Case-insensitive name search |
| `min_price` | integer | none | Minor units, 0 or more. Matches if **any** variant is at or above it |
| `max_price` | integer | none | Minor units, 0 or more. Must not be below `min_price` (otherwise `422`) |
| `scent_family` | string | none | Matches `attributes.scent_family` (fragrance) |
| `skin_type` | string | none | Matches `attributes.skin_types` |
| `page` | integer | `1` | 1 or more |
| `page_size` | integer | `20` | 1 to 100 |

Results are sorted newest first. Because the default status is `published`, draft and archived products only appear when requested explicitly.

Response:

```json
{
  "items": [
    {
      "id": "a5a6cf80-4b5b-465b-9615-5ddec43466f7",
      "slug": "velvet-matte-lipstick",
      "name": "Velvet Matte Lipstick",
      "brand": "Elles",
      "category": "makeup",
      "status": "draft",
      "image": null,
      "price_from": { "amount": 185000, "currency": "KES" },
      "variant_count": 1
    }
  ],
  "total": 4,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

`price_from` is the cheapest **active** variant, and `variant_count` counts active variants only.

### Get a product: `GET /{slug}`

Returns the full product: `id`, `slug`, `name`, `brand`, `category`, `description`, `benefits`, `how_to_use`, `attributes`, `variants` (each with `sku`, `shade_name`, `size`, `price`, `images`, `is_active`), `images`, `status`, `created_at` and `updated_at`. An unknown slug returns `404`.

### Publish and archive

`POST /{slug}/publish` applies the domain rule: the product needs a name, a slug and at least one active variant. If the rule fails the response is `409 Conflict` with the reason. `POST /{slug}/archive` moves the product to `archived`. Both return the full product. Archived products keep their slug and SKUs reserved.

### Create a product: `POST /`

The admin ID is currently read from the `X-Admin-Id` header, with a hardcoded fallback. This is a temporary stand-in for the JWT guard (see Known gaps). The response is a short confirmation:

```json
{
  "message": "Product draft created successfully",
  "product_id": "<uuid>",
  "status": "draft",
  "name": "Velvet Matte Lipstick"
}
```

## Create request schema

The request is a **discriminated union on `category`**: each category has its own request model with its own typed `attributes`. A wrong or missing category returns `422` listing the allowed values.

### Common fields

| Field | Type | Rules |
|---|---|---|
| `slug` | string | 3 to 200 chars, lowercase letters, digits and hyphens (`my-product`). Unique |
| `name` | string | 3 to 200 chars |
| `brand` | string | 2 to 100 chars |
| `category` | enum | One of the seven categories |
| `description` | string | 10 to 5000 chars |
| `benefits` | string[] | Optional |
| `how_to_use` | string[] | Optional. One entry per step |
| `attributes` | object | Typed per category (below) |
| `variants` | `VariantDTO[]` | At least one. SKUs unique within the request |
| `images` | string[] | Optional |
| `status` | `"draft"` | Only `draft` is accepted on create |

All request models strip whitespace and **reject unknown fields**, so a typo such as `how_too_use` returns `422` instead of being ignored.

### `VariantDTO`

| Field | Type | Rules |
|---|---|---|
| `sku` | string | 1 to 64 chars. Unique across all products |
| `price` | `PriceDTO` | Required |
| `shade_name` | string | Optional |
| `size` | `SizeDTO` | Optional |
| `images` | string[] | Optional |
| `is_active` | bool | Default `true` |

`PriceDTO`: `amount` is an integer greater than 0 in **minor units** (`18500` = KES 185.00), and `currency` is a 3-letter ISO code, uppercased, default `KES`. `SizeDTO`: `value` is a number greater than 0, and `unit` defaults to `ml`.

### `attributes` per category

| Category | Fields |
|---|---|
| `makeup` | `finish`, `coverage`, `skin_types[]`, `claims[]` |
| `fragrance` | `concentration` (**required**), `gender_target`, `scent_family[]`, `notes{top,heart,base}`, `longevity` |
| `skincare` | `skin_types[]`, `key_ingredients[]`, `spf` |
| `haircare` | `hair_types[]`, `key_ingredients[]` |
| `bodycare` | `skin_types[]`, `key_ingredients[]`, `scent` |
| `nails` | `finish`, `claims[]` |
| `tools` | `material`, `reusable` |

Fragrance variants must each have a `size`. Adding a category means adding an attributes class, a request class and an entry in the union.

### Example request

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

## Architecture

```
presentation/api/products.py              Routes and error mapping
application/dtos/product_dtos.py          Create request models (discriminated union)
application/dtos/product_responses.py     ProductResponse, ProductSummary, ProductListResponse
application/use_cases/create_product.py   CreateProductUseCase
application/use_cases/product_queries.py  ListProductsUseCase, GetProductBySlugUseCase
application/use_cases/product_status.py   PublishProductUseCase, ArchiveProductUseCase
application/ports/repositories.py         ProductRepositoryPort, ProductFilters
domain/models/product.py                  Product, Variant, Price, Size, ProductStatus
infrastructure/persistence/mongodb/       MongoProductRepository, database client
infrastructure/config.py                  Settings
```

## Domain rules

- `Price.amount` must be greater than 0.
- `Product.publish()` requires a name, a slug and at least one active variant.
- `Product.archive()` moves the product to `archived`.
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
| `category`, `status` | Filtering |
| `status`, `category`, `created_at` | Default list query and sort |
| `brand` | Brand filter |
| `variants.price.amount` | Price range filter |
| `attributes.scent_family`, `attributes.skin_types` | Category filters |

The use case checks the slug before saving, but two simultaneous requests could both pass that check. The unique indexes are the real guarantee: the repository catches `DuplicateKeyError` and re-raises it as a domain exception.

## Configuration

| Variable | Description | Default |
|---|---|---|
| `ENVIRONMENT` | Runtime environment | `local` |
| `MONGO_URL` | MongoDB connection string | `mongodb://admin:admin@localhost:27017/?authSource=admin` |
| `MONGODB_DB_NAME` | Database name | `catalog_db` |

Settings are case-sensitive, so the variable must be named exactly `MONGO_URL`. In Docker Compose the host is `mongodb`, not `localhost`.

## Running and verifying

```bash
cd backend/catalog-service
uvicorn catalog_app.main:app --host 0.0.0.0 --port 8005 --reload
```

Open `http://localhost:8005/docs`, create a product, then:

```bash
curl "http://localhost:8005/api/v1/products/?status=draft"
curl -X POST http://localhost:8005/api/v1/products/velvet-matte-lipstick/publish
curl "http://localhost:8005/api/v1/products/"
```

The last call should now return the published product.

## Known gaps

- **Auth:** `created_by` comes from an unauthenticated `X-Admin-Id` header with a hardcoded fallback. Create, publish and archive need a JWT admin guard. Non-published listings should be admin-only.
- **Duplicate slug or SKU on create returns `400`.** Map it to `409` in a global exception handler.
- No update endpoint (edit name, description, variants) yet.
- Sorting is newest first only. Price sorting needs a stored minimum price on the product.
- Automated tests for the filters, the union and the publish rules.
