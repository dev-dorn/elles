# Catalog Service: Products API

Documents the product endpoints in `catalog-service`: create, list, get, publish and archive, with authentication, request and response schemas, error codes, storage and configuration.

## Overview

The catalog models a **product with variants**. A product holds the shared information (name, brand, benefits, how to use). Each variant is a purchasable item with its own SKU, price and images. A variant is a shade (makeup, nails) or a size (fragrance, skincare, haircare, bodycare), or neither (tools).

All categories live in **one `products` collection**. Category-specific data goes in `attributes`, validated per category (see below). Stock is **not** stored in the catalog: quantities belong to `inventory-service` and are joined on `sku`.

## Authentication

Write endpoints need an **admin** access token issued by `identity-service` (`POST /api/v1/auth/login`), sent as:

```
Authorization: Bearer <access_token>
```

The catalog verifies the token itself; it does not call identity-service. A token is accepted when:

- its signature verifies with `JWT_SECRET_KEY` using the configured algorithm (default `HS256`). The secret must be **identical** in identity-service and catalog-service;
- it has `exp` (not expired) and `sub` (a UUID);
- its `role` (or `roles`) claim contains `admin`, compared case-insensitively.

`created_by` on a new product is taken from the token's `sub`. It is never accepted from the request body or a header.

| Situation | Response |
|---|---|
| No token on a protected endpoint | `401` `Not authenticated` |
| Bad signature or missing `exp`/`sub` | `401` `Invalid token` |
| Expired token | `401` `Token has expired` |
| `sub` is not a UUID | `401` `Invalid token subject` |
| Valid token without the admin role | `403` `Admin access required` |

Reading is public, with one restriction: only **published** products are visible without an admin token (see the list and get endpoints).

## Endpoints

Base path: `/api/v1/products` (local uvicorn: `http://localhost:8005`, Docker: `http://localhost:8001`)

| Method | Path | Access | Purpose | Success |
|---|---|---|---|---|
| `POST` | `/` | Admin | Create a product (always starts as `draft`) | `201` |
| `GET` | `/` | Public (published) / Admin (other statuses) | List with filters and pagination | `200` |
| `GET` | `/{slug}` | Public (published) / Admin (any) | Get one product | `200` |
| `POST` | `/{slug}/publish` | Admin | Move to `published` | `200` |
| `POST` | `/{slug}/archive` | Admin | Move to `archived` | `200` |

### Error responses

| Status | When |
|---|---|
| `400` | A domain rule is broken (for example a price of 0 or less) |
| `401` / `403` | Authentication or authorization failure (see above) |
| `404` | Unknown slug, or an unpublished product requested without an admin token |
| `409` | Duplicate slug or SKU on create, or a publish rule not met |
| `422` | Invalid body or query parameters |

All errors use the shape `{"detail": "..."}`.

### List products: `GET /`

Query parameters:

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `category` | enum | none | `makeup`, `fragrance`, `skincare`, `haircare`, `bodycare`, `nails`, `tools` |
| `brand` | string | none | Exact match |
| `status` | enum | `published` | `draft`, `published` or `archived`. Anything other than `published` needs an admin token, otherwise `403` |
| `q` | string | none | 2 to 100 chars. Case-insensitive name search |
| `min_price` | integer | none | Minor units, 0 or more. Matches if **any** variant is at or above it |
| `max_price` | integer | none | Minor units, 0 or more. Must not be below `min_price` (otherwise `422`) |
| `scent_family` | string | none | Matches `attributes.scent_family` (fragrance) |
| `skin_type` | string | none | Matches `attributes.skin_types` |
| `page` | integer | `1` | 1 or more |
| `page_size` | integer | `20` | 1 to 100 |

Results are sorted newest first.

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
      "status": "published",
      "image": null,
      "price_from": { "amount": 185000, "currency": "KES" },
      "variant_count": 1
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

`price_from` is the cheapest **active** variant, and `variant_count` counts active variants only.

### Get a product: `GET /{slug}`

Returns the full product: `id`, `slug`, `name`, `brand`, `category`, `description`, `benefits`, `how_to_use`, `attributes`, `variants` (each with `sku`, `shade_name`, `size`, `price`, `images`, `is_active`), `images`, `status`, `created_at` and `updated_at`.

A product that is not `published` returns `404` to anyone without an admin token, so unpublished products are not revealed.

### Publish and archive

`POST /{slug}/publish` applies the domain rule: the product needs a name, a slug and at least one active variant. If the rule fails the response is `409 Conflict` with the reason. `POST /{slug}/archive` moves the product to `archived`. Both return the full product and need an admin token. An archived product can be published again directly. Archived products keep their slug and SKUs reserved.

### Create a product: `POST /`

Needs an admin token. Duplicate slugs or SKUs return `409`. A successful call returns a short confirmation:

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
  "slug": "golden-hour-eau-de-parfum",
  "name": "Golden Hour Eau de Parfum",
  "brand": "Elles",
  "category": "fragrance",
  "description": "A warm, sunlit fragrance with citrus, jasmine and soft amber.",
  "benefits": ["Long-lasting", "Everyday wear"],
  "how_to_use": ["Spray on pulse points: wrists, neck and behind the ears."],
  "attributes": {
    "concentration": "eau-de-parfum",
    "gender_target": "women",
    "scent_family": ["floral", "warm"],
    "notes": { "top": ["bergamot"], "heart": ["jasmine"], "base": ["amber", "musk"] }
  },
  "variants": [
    {
      "sku": "ELL-FRG-GH-50",
      "size": { "value": 50, "unit": "ml" },
      "price": { "amount": 850000, "currency": "KES" },
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
  -H "Authorization: Bearer $TOKEN" \
  -d @product.json
```

## Architecture

```
presentation/api/products.py              Routes
presentation/api/security.py              JWT guard: require_admin, optional_admin
main.py                                   App, lifespan (indexes), exception handlers
application/dtos/product_dtos.py          Create request models (discriminated union)
application/dtos/product_responses.py     ProductResponse, ProductSummary, ProductListResponse
application/use_cases/create_product.py   CreateProductUseCase
application/use_cases/product_queries.py  ListProductsUseCase, GetProductBySlugUseCase
application/use_cases/product_status.py   PublishProductUseCase, ArchiveProductUseCase
application/ports/repositories.py         ProductRepositoryPort, ProductFilters
domain/models/product.py                  Product, Variant, Price, Size, ProductStatus
domain/exceptions.py                      DomainException, InvalidPriceError, DuplicateProductError
infrastructure/persistence/mongodb/       MongoProductRepository, database client
infrastructure/config.py                  Settings
```

Domain exceptions are mapped to HTTP in `main.py`: `DuplicateProductError` returns `409`, and any other `DomainException` (including `InvalidPriceError`) returns `400`. The publish route catches `DomainException` itself and returns `409`, because a failed publish rule is a state conflict.

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
- Datetimes are stored in UTC.

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

The use case checks the slug before saving, but two simultaneous requests could both pass that check. The unique indexes are the real guarantee: the repository catches `DuplicateKeyError` and raises `DuplicateProductError`, which returns the same `409`. If index creation fails at startup, existing documents contain a duplicate slug or SKU and must be fixed first.

## Configuration

Set these in `catalog-service/.env` (never commit it):

| Variable | Description | Default |
|---|---|---|
| `ENVIRONMENT` | Runtime environment | `local` |
| `MONGO_URL` | MongoDB connection string | `mongodb://admin:admin@localhost:27017/?authSource=admin` |
| `MONGODB_DB_NAME` | Database name | `catalog_db` |
| `JWT_SECRET_KEY` | Secret used to verify tokens. **Required, no default**. Must equal identity-service's value | none |
| `JWT_ALGORITHM` | Token algorithm | `HS256` |
| `ADMIN_ROLE` | Role name that grants write access | `admin` |

Settings are case-sensitive, so names must match exactly; unknown variables are ignored. A missing `JWT_SECRET_KEY` stops the app at startup on purpose. Generate a secret with `openssl rand -hex 32`.

In Docker Compose the Mongo host is `mongodb`, not `localhost`, and `JWT_SECRET_KEY` must be passed to both identity-service and catalog-service from `infrastructure/.env`. A `.env` change needs a service restart (uvicorn's reloader only watches Python files); after changing the secret, log in again, because tokens signed with the old one no longer verify.

## Running and verifying

```bash
cd backend/catalog-service
uvicorn catalog_app.main:app --host 0.0.0.0 --port 8005 --reload
```

Get a token, then create, publish and read:

```bash
TOKEN=$(curl -s -X POST http://localhost:8004/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"<admin email>","password":"<password>"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -X POST http://localhost:8005/api/v1/products/golden-hour-eau-de-parfum/publish \
  -H "Authorization: Bearer $TOKEN"

curl "http://localhost:8005/api/v1/products/"
```

Checks that should hold:

- Create without a token returns `401`; the same slug twice returns `409`.
- `GET /?status=draft` without a token returns `403`; with an admin token it returns drafts.
- A draft requested by slug without a token returns `404`.
- After publishing, the product appears in the public list.

Access tokens are short-lived, so log in again if you get `Token has expired`.

## Known gaps

- Tokens carry a `type` claim that is not checked yet; require `access` so other token types cannot be used here.
- Set `tz_aware=True` on the Motor client so `created_at` is returned with a `Z` suffix like `updated_at`.
- The create endpoint returns a short confirmation, not the full `ProductResponse`.
- No update endpoint (edit name, description, variants) yet.
- Sorting is newest first only. Price sorting needs a stored minimum price on the product.
- Automated tests for the filters, the union, the guard and the publish rules.
