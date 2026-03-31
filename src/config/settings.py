from pydantic import model_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    USER: str = "dev"
    PASSWORD: str = "store"
    HOST: str = "database"
    PORT: int = 5432
    NAME: str = "dev"
    POOL_SIZE: int = 15
    POOL_RECYCLE: int = 1800
    POSTGRES_CONNECTION_STRING: str | None = Field(
        None, alias="POSTGRES_CONNECTION_STRING"
    )

    DSN: str = ""

    @model_validator(mode="after")
    def build_dsn(self) -> "DatabaseSettings":
        """Собираем DSN из компонентов или используем готовый"""
        if self.POSTGRES_CONNECTION_STRING:
            self.DSN = self.POSTGRES_CONNECTION_STRING
        else:
            self.DSN = (
                f"postgresql+asyncpg://{self.USER}:{self.PASSWORD}"
                f"@{self.HOST}:{self.PORT}/{self.NAME}"
            )
        return self


class KafkaSettings(BaseSettings):
    BOOTSTRAP_SERVERS: str = "localhost:9092"
    TOPUC: str = "orders"


class CatalogSettings(BaseSettings):
    BASE_URL: str = "http://catalog-service:8000"
    API_KEY: str = "api_key"

    model_config = SettingsConfigDict(env_prefix="CATALOG_")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    db: DatabaseSettings = DatabaseSettings()
    kafka: KafkaSettings = KafkaSettings()
    catalog: CatalogSettings = CatalogSettings()


settings = Settings()
