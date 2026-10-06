import os
import subprocess
import textwrap
from pathlib import Path

# ==========================================
# CONFIGURATION
# ==========================================
ROOT_DIR = Path("elles")
SERVICES = {
    "catalog-service": {"db": "mongo", "port": 8001, "desc": "Catalog & Discovery (Products, Scent Notes)"},
    "order-service": {"db": "postgres", "port": 8002, "desc": "Order & Checkout (Carts, Orders)"},
    "inventory-service": {"db": "postgres", "port": 8003, "desc": "Inventory & Warehouse (Stock, Batches)"},
    "identity-service": {"db": "postgres", "port": 8004, "desc": "Identity & Access (Users, Auth)"},
    "payment-service": {"db": "postgres", "port": 8005, "desc": "Payment & Billing (Transactions)"},
    "notification-service": {"db": "mongo", "port": 8006, "desc": "Notification & Shipping (Receipts, Emails)"},
}

def create_file(path: Path, content: str):
    """Creates a file and its parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip())
    print(f"  -> Created {path}")

# ==========================================
# 1. FRONTEND (Next.js)
# ==========================================
def setup_frontend():
    print("\n[1/4] Setting up Next.js Frontend...")
    frontend_dir = ROOT_DIR / "frontend"
    if not frontend_dir.exists():
        # Run create-next-app
        cmd = [
            "npx", "create-next-app@latest", "frontend", 
            "--typescript", "--tailwind", "--eslint", "--app", "--src-dir", "--use-npm"
        ]
        subprocess.run(cmd, cwd=ROOT_DIR, check=True)
    else:
        print("  -> Frontend directory already exists. Skipping.")

# ==========================================
# 2. BACKEND MICROSERVICES (FastAPI)
# ==========================================
def setup_backend():
    print("\n[2/4] Setting up FastAPI Microservices...")
    
    for service_name, config in SERVICES.items():
        print(f"\n  Building {service_name}...")
        base_path = ROOT_DIR / "backend" / service_name
        app_path = base_path / "app"
        
        # Create Clean Architecture Directories
        layers = ["domain/models", "domain/services", "application/ports", "application/use_cases", "application/dtos", 
                  "infrastructure/persistence", "infrastructure/messaging", "infrastructure/aws", "presentation/api", "presentation/consumers"]
        
        for layer in layers:
            (app_path / layer).mkdir(parents=True, exist_ok=True)
            create_file(app_path / layer / "__init__.py", "")
        
        # 1. requirements.txt
        db_deps = "sqlalchemy[asyncio]==2.0.27\nasyncpg==0.29.0\nalembic==1.13.1" if config["db"] == "postgres" else "motor==3.3.2\nbeanie==1.25.0"
        create_file(base_path / "requirements.txt", f"""
            fastapi==0.110.0
            uvicorn[standard]==0.27.1
            pydantic==2.6.1
            pydantic-settings==2.1.0
            {db_deps}
            aio-pika==9.4.0
            aioboto3==12.3.0
            python-dotenv==1.0.1
            orjson==3.9.15
        """)

        # 2. Dockerfile
        create_file(base_path / "Dockerfile", f"""
            FROM python:3.11-slim
            ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
            WORKDIR /app
            RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*
            COPY requirements.txt .
            RUN pip install --upgrade pip && pip install -r requirements.txt
            COPY . .
            EXPOSE 8000
            CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
        """)

        # 3. app/infrastructure/config.py (Pydantic Settings)
        db_url_env = "POSTGRES_URL" if config["db"] == "postgres" else "MONGO_URI"
        create_file(app_path / "infrastructure" / "config.py", f"""
            from pydantic_settings import BaseSettings

            class Settings(BaseSettings):
                ENVIRONMENT: str = "local"
                {db_url_env}: str
                RABBITMQ_URL: str = "amqp://admin:admin@rabbitmq:5672/"
                AWS_ENDPOINT_URL: str = "http://localstack:4566"
                AWS_ACCESS_KEY_ID: str = "test"
                AWS_SECRET_ACCESS_KEY: str = "test"
                
                class Config:
                    env_file = ".env"

            settings = Settings()
        """)

        # 4. app/domain/events.py (Pure Python Domain Events)
        create_file(app_path / "domain" / "events.py", """
            from dataclasses import dataclass
            from datetime import datetime
            from uuid import UUID, uuid4

            @dataclass(frozen=True)
            class DomainEvent:
                event_id: UUID
                occurred_on: datetime
                aggregate_id: UUID
                correlation_id: str

                @classmethod
                def create(cls, aggregate_id: UUID, correlation_id: str, **kwargs):
                    return cls(
                        event_id=uuid4(),
                        occurred_on=datetime.utcnow(),
                        aggregate_id=aggregate_id,
                        correlation_id=correlation_id,
                        **kwargs
                    )
        """)

        # 5. app/main.py (FastAPI App Factory)
        create_file(app_path / "main.py", f"""
            from fastapi import FastAPI
            from contextlib import asynccontextmanager
            from app.infrastructure.config import settings

            @asynccontextmanager
            async def lifespan(app: FastAPI):
                print(f"Starting {service_name} | DB: {config['db']}")
                # TODO: Initialize Async DB pools and RabbitMQ connections here
                yield
                print(f"Shutting down {service_name}...")

            app = FastAPI(
                title="{service_name.replace('-', ' ').title()}",
                description="{config['desc']}",
                version="1.0.0",
                lifespan=lifespan
            )

            @app.get("/health")
            async def health_check():
                return {{"status": "healthy", "service": "{service_name}"}}
        """)

# ==========================================
# 3. INFRASTRUCTURE (Docker & LocalStack)
# ==========================================
def setup_infrastructure():
    print("\n[3/4] Setting up Docker Infrastructure...")
    infra_dir = ROOT_DIR / "infrastructure"
    infra_dir.mkdir(parents=True, exist_ok=True)

    # docker-compose.yml
    services_yaml = ""
    for svc, cfg in SERVICES.items():
        db_dep = "mongodb" if cfg["db"] == "mongo" else "postgres"
        db_url = f"mongodb://admin:admin@mongodb:27017" if cfg["db"] == "mongo" else f"postgresql+asyncpg://admin:admin@postgres:5432/{svc.replace('-service', '_db')}"
        
        services_yaml += f"""
  {svc}:
    build: ../backend/{svc}
    ports:
      - "{cfg['port']}:8000"
    environment:
      - ENVIRONMENT=local
      - {'MONGO_URI' if cfg['db'] == 'mongo' else 'POSTGRES_URL'}={db_url}
      - RABBITMQ_URL=amqp://admin:admin@rabbitmq:5672/
      - AWS_ENDPOINT_URL=http://localstack:4566
    depends_on:
      {db_dep}:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
"""

    create_file(infra_dir / "docker-compose.yml", f"""
        version: '3.9'

        services:
          postgres:
            image: postgres:15-alpine
            environment:
              POSTGRES_USER: admin
              POSTGRES_PASSWORD: admin
            ports:
              - "5432:5432"
            volumes:
              - postgres_data:/var/lib/postgresql/data
            healthcheck:
              test: ["CMD-SHELL", "pg_isready -U admin"]
              interval: 5s
              timeout: 5s
              retries: 5

          mongodb:
            image: mongo:7.0
            environment:
              MONGO_INITDB_ROOT_USERNAME: admin
              MONGO_INITDB_ROOT_PASSWORD: admin
            ports:
              - "27017:27017"
            volumes:
              - mongo_data:/data/db
            healthcheck:
              test: echo 'db.runCommand("ping").ok' | mongosh --quiet
              interval: 5s
              timeout: 5s
              retries: 5

          rabbitmq:
            image: rabbitmq:3-management-alpine
            environment:
              RABBITMQ_DEFAULT_USER: admin
              RABBITMQ_DEFAULT_PASS: admin
            ports:
              - "5672:5672"
              - "15672:15672"
            volumes:
              - rabbitmq_data:/var/lib/rabbitmq
            healthcheck:
              test: rabbitmq-diagnostics -q ping
              interval: 10s
              timeout: 10s
              retries: 5

          localstack:
            image: localstack/localstack:latest
            ports:
              - "4566:4566"
            environment:
              - SERVICES=s3
              - DEFAULT_REGION=us-east-1
            volumes:
              - localstack_data:/var/lib/localstack
        {services_yaml}
          nextjs-frontend:
            build: ../frontend
            ports:
              - "3000:3000"
            environment:
              - NEXT_PUBLIC_CATALOG_API=http://localhost:8001
            depends_on:
              - catalog-service
              - order-service

        volumes:
          postgres_data:
          mongo_data:
          rabbitmq_data:
          localstack_data:
    """)

# ==========================================
# 4. ROOT FILES
# ==========================================
def setup_root():
    print("\n[4/4] Setting up Root Files...")
    create_file(ROOT_DIR / ".gitignore", """
        __pycache__/
        *.py[cod]
        .env
        .venv/
        node_modules/
        .next/
        *.log
    """)
    
    create_file(ROOT_DIR / "README.md", """
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
    """)

# ==========================================
# EXECUTION
# ==========================================
if __name__ == "__main__":
    print("🚀 Initializing ELLES E-Commerce Monorepo...")
    ROOT_DIR.mkdir(exist_ok=True)
    
    setup_root()
    setup_backend()
    setup_infrastructure()
    setup_frontend() # Run last as it takes the longest and requires npm
    
    print("\n✅ SUCCESS! The 'elles' project has been fully scaffolded.")
    print("👉 Next steps:")
    print("   1. cd elles/infrastructure")
    print("   2. docker-compose up --build")