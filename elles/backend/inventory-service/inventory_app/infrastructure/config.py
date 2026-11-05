from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENVIRONMENT: str = "local"
    POSTGRES_URL: str = "postgresql+asyncpg://admin:admin@localhost:5432/inventory_db"
    RABBITMQ_URL: str = "amqp://admin:admin@rabbitmq:5672/"
    AWS_ENDPOINT_URL: str = "http://localstack:4566"
    AWS_ACCESS_KEY_ID: str = "test"
    AWS_SECRET_ACCESS_KEY: str = "test"
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ADMIN_ROLE: str = "admin"
    SERVICE_ROLE: str = "service"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra="ignore"

settings = Settings()
