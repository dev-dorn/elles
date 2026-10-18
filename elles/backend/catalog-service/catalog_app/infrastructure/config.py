
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "local"
    MONGODB_URL: str = "mongodb://admin:admin@localhost:27017"
    MONGODB_DB_NAME : str= "catalog_db"

    model_config= SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
