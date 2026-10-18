from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENVIRONMENT: str = "local"
    POSTGRES_URL: str
    RABBITMQ_URL: str = "amqp://admin:admin@rabbitmq:5672/"
    AWS_ENDPOINT_URL: str = "http://localstack:4566"
    AWS_ACCESS_KEY_ID: str = "test"
    AWS_SECRET_ACCESS_KEY: str = "test"

    class Config:
        env_file = ".env"

settings = Settings()
