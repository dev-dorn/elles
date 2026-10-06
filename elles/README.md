# Elles - Luxury Perfume E-Commerce
A production-grade, distributed e-commerce platform built with FastAPI, Next.js, and AWS.

## Architecture
- **Frontend:** Next.js (BFF / Logical Gateway)
- **Backend:** 6 FastAPI Microservices (Clean Architecture / Hexagonal)
- **Messaging:** RabbitMQ (Event-Driven Architecture)
- **Persistence:** Polyglot (PostgreSQL for Transactions, MongoDB for Catalog/Receipts)

## Local Development
1. Ensure Docker and Node.js are installed.
2. Run `cd infrastructure && docker-compose up --build`
3. Access services:
   - Frontend: http://localhost:3000
   - RabbitMQ UI: http://localhost:15672 (admin/admin)
