# Inventory service

This service provides the inventory API skeleton, a health endpoint, JWT authentication and role checks, and foundational stock item persistence. Stock adjustments, movement ledger APIs, and reservations are tracked in later inventory milestones.

## Run the service

For Docker Compose, set `JWT_SECRET_KEY` in `elles/infrastructure/.env` to a strong secret shared with the identity service, then run:

```bash
cd elles/infrastructure
docker compose up -d --build inventory-service
```

The API is available at `http://localhost:8003`; interactive API docs are at `http://localhost:8003/docs`.

To run from the local virtual environment instead, set `JWT_SECRET_KEY` in `elles/backend/inventory-service/.env` to the same value used by identity, activate the project virtual environment, and run from the inventory service directory:

```bash
uvicorn inventory_app.main:app --host 0.0.0.0 --port 8003 --reload
```

Only one process can listen on port `8003` at a time. Stop the Compose service before starting Uvicorn locally, or stop the local Uvicorn process before starting the Compose service.

## Endpoints

| Method | Path | Authorization | Purpose |
| --- | --- | --- | --- |
| `GET` | `/health` | None | Returns the service health response. |
| `GET` | `/api/v1/auth-check/whoami` | Any valid access token | Returns the token subject and normalized roles. |
| `GET` | `/api/v1/auth-check/admin` | `admin` role | Checks an admin-only route. |
| `GET` | `/api/v1/auth-check/admin-or-service` | `admin` or `service` role | Checks a route available to admins and services. |

`/health` checks PostgreSQL and returns `503 Service Unavailable` if the database cannot answer. The three `/auth-check` routes are temporary authorization checks. They return `401 Unauthorized` when the bearer token is missing or invalid, and role-restricted routes return `403 Forbidden` when the token is valid but lacks an allowed role.

## Database connection and migrations

`POSTGRES_URL` uses SQLAlchemy's async driver format. For a local service process, the default is `postgresql+asyncpg://admin:admin@localhost:5433/inventory_db`; set it in the service `.env` if your PostgreSQL port or credentials differ. Docker Compose supplies the internal URL `postgresql+asyncpg://admin:admin@postgres-inventory:5432/inventory_db`.

The async engine and session factory live in `inventory_app/infrastructure/persistence/postgres/database.py`. Database availability is checked during startup and by `/health`; the engine is disposed during shutdown.

Run migrations from the inventory service directory with the project virtual environment active:

```bash
alembic upgrade head
alembic downgrade base
```

The initial revision is intentionally empty. Revision `0002_stock_items` creates `stock_items` with database checks for nonnegative `on_hand` and `reserved`, and for `reserved <= on_hand`. `alembic downgrade base` drops `stock_items` and removes the baseline revision.

## Stock item model and repository

`StockItem` represents one SKU with `on_hand`, `reserved`, and `updated_at`. Its `available` property is computed as `on_hand - reserved`. The domain model rejects blank SKUs, negative quantities, and reservations greater than on-hand stock.

The PostgreSQL `stock_items` table stores `sku` as its primary key. Check constraints enforce the quantity invariants in the database too, so invalid stock cannot be persisted even when a write bypasses domain validation.

`PostgresStockRepository` provides two read operations:

- `get_stock(sku)` returns the matching domain object or `None`.
- `get_stock_many(skus)` returns a mapping keyed by matching SKU. Missing SKUs are omitted, duplicate inputs are collapsed, and an empty input returns an empty mapping.

The repository contract tests run the same read cases against an in-memory fake and PostgreSQL. Additional PostgreSQL cases verify that the database rejects invalid quantities. The tests were run against the separate `inventory_test_db` database.

## Repository contract tests

Install development dependencies with `pip install -r requirements-dev.txt`, then run the repository tests. The same read tests run against the in-memory fake and PostgreSQL. PostgreSQL cases are enabled by setting `INVENTORY_TEST_POSTGRES_URL` to a dedicated test database URL. The test fixture drops and recreates `stock_items`, so do not point it at a development or production database.

Example, after creating a separate `inventory_test_db` database:

```bash
INVENTORY_TEST_POSTGRES_URL='postgresql+asyncpg://admin:admin@localhost:5433/inventory_test_db' \
  pytest -q tests/test_stock_repository.py
```

## JWT configuration

Inventory verifies tokens with `PyJWT`, using `JWT_SECRET_KEY` and `JWT_ALGORITHM` (defaults to `HS256`). The identity service must sign access tokens with the same secret and algorithm. Keep the secret in an ignored `.env` file or an equivalent secret store; do not commit it.

Tokens must include `exp` and `sub`; `sub` must be a UUID. Role checks read `role` or `roles` and compare values in lowercase. Use the `access_token` returned by identity login, not the refresh token. Log in again after rotating the shared secret because tokens signed with the previous secret will fail verification.

Example request:

```bash
curl -i http://localhost:8003/api/v1/auth-check/whoami \
  -H "Authorization: Bearer $TOKEN"
```

For Postman, choose **Bearer Token** authorization and paste only the `access_token` value.
