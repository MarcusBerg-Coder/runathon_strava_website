from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_url: str = Field(default="http://localhost:3000", alias="NEXT_PUBLIC_APP_URL")
    api_public_url: str | None = Field(default=None, alias="API_PUBLIC_URL")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")

    admin_password: str | None = Field(default=None, alias="ADMIN_PASSWORD")
    admin_session_secret: str = Field(default="dev-only-change-me", alias="ADMIN_SESSION_SECRET")

    paypal_env: str = Field(default="sandbox", alias="PAYPAL_ENV")
    paypal_client_id: str | None = Field(default=None, alias="PAYPAL_CLIENT_ID")
    paypal_client_secret: str | None = Field(default=None, alias="PAYPAL_CLIENT_SECRET")
    paypal_webhook_id: str | None = Field(default=None, alias="PAYPAL_WEBHOOK_ID")

    strava_client_id: str | None = Field(default=None, alias="STRAVA_CLIENT_ID")
    strava_client_secret: str | None = Field(default=None, alias="STRAVA_CLIENT_SECRET")
    strava_verify_token: str = Field(default="dev-verify-token", alias="STRAVA_VERIFY_TOKEN")
    strava_token_encryption_key: str | None = Field(default=None, alias="STRAVA_TOKEN_ENCRYPTION_KEY")

    model_config = SettingsConfigDict(
        env_file=(".env.local", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def paypal_base_url(self) -> str:
        if self.paypal_env.lower() == "live":
            return "https://api-m.paypal.com"
        return "https://api-m.sandbox.paypal.com"

    @property
    def async_database_url(self) -> str | None:
        if not self.database_url:
            return None
        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.database_url

    @property
    def public_api_base_url(self) -> str:
        if self.api_public_url:
            return self.api_public_url.rstrip("/")
        return f"{self.app_url.rstrip('/')}/api"


@lru_cache
def get_settings() -> Settings:
    return Settings()
