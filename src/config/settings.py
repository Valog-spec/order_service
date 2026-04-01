from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    DB_USER: str = "dev"
    PASSWORD: str = "store"
    HOST: str = "database"
    PORT: int = 5432
    NAME: str = "dev"
    POOL_SIZE: int = 15
    POOL_RECYCLE: int = 1800
    POSTGRES_CONNECTION_STRING: str | None = None

    DSN: str = ""

    @model_validator(mode="after")
    def build_dsn(self) -> "DatabaseSettings":
        """Собираем DSN из компонентов или используем готовый"""
        if self.POSTGRES_CONNECTION_STRING:
            dsn = self.POSTGRES_CONNECTION_STRING

            if dsn.startswith("postgres://"):
                dsn = dsn.replace("postgres://", "postgresql+asyncpg://", 1)
            elif dsn.startswith("postgresql://") and "+asyncpg" not in dsn:
                dsn = dsn.replace("postgresql://", "postgresql+asyncpg://", 1)
            self.DSN = dsn
        else:
            self.DSN = (
                f"postgresql+asyncpg://{self.DB_USER}:{self.PASSWORD}"
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


class PaymentSettings(BaseSettings):
    BASE_URL: str = "http://payment-service:8000"
    API_KEY: str = "api_key"
    CALLBACK_URL: str = "http://student-valog-spec-order-service-web.student-valog-spec-order-service.svc:8000/api/orders/payment-callback"

    model_config = SettingsConfigDict(env_prefix="PAYMENT_")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    db: DatabaseSettings = DatabaseSettings()
    kafka: KafkaSettings = KafkaSettings()
    catalog: CatalogSettings = CatalogSettings()
    payment: PaymentSettings = PaymentSettings()


settings = Settings()
