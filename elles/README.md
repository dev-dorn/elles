# Elles - Luxury Perfume E-Commerce
A production-grade, distributed e-commerce platform built with FastAPI, Next.js, and AWS.

## Architecture
- **Frontend:** Next.js (BFF / Logical Gateway)
- **Backend:** 6 FastAPI Microservices (Clean Architecture / Hexagonal)
- **Messaging:** RabbitMQ (Event-Driven Architecture)
- **Persistence:** Polyglot (PostgreSQL for Transactions, MongoDB for Catalog/Receipts)

## Local Development
1. Ensure Docker and Node.js are installed.
2. Create `infrastructure/.env` with a strong `JWT_SECRET_KEY` value. Keep secrets out of source control.
3. Run `cd infrastructure && docker compose up --build`
4. Access services:
   - RabbitMQ UI: http://localhost:15672 (admin/admin)
   - Inventory API: http://localhost:8003
   - Inventory API docs: http://localhost:8003/docs

See the [inventory service guide](backend/inventory-service/README.md) for its health endpoint, JWT requirements, role checks, and local run instructions.

The frontend is not currently included in the Docker Compose setup.
