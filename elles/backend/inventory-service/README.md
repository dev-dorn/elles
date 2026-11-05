# Inventory service

This service currently provides the inventory API skeleton, a health endpoint, and JWT authentication and role checks. Stock persistence and operations are tracked in the next inventory milestones.

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

The initial revision is intentionally empty. `upgrade head` records the Alembic baseline in `alembic_version`; inventory tables will be introduced by a later migration.

## JWT configuration

Inventory verifies tokens with `PyJWT`, using `JWT_SECRET_KEY` and `JWT_ALGORITHM` (defaults to `HS256`). The identity service must sign access tokens with the same secret and algorithm. Keep the secret in an ignored `.env` file or an equivalent secret store; do not commit it.

Tokens must include `exp` and `sub`; `sub` must be a UUID. Role checks read `role` or `roles` and compare values in lowercase. Use the `access_token` returned by identity login, not the refresh token. Log in again after rotating the shared secret because tokens signed with the previous secret will fail verification.

Example request:

```bash
curl -i http://localhost:8003/api/v1/auth-check/whoami \
  -H "Authorization: Bearer $TOKEN"
```

For Postman, choose **Bearer Token** authorization and paste only the `access_token` value.
