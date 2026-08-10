from __future__ import annotations

from functools import lru_cache
from zoneinfo import ZoneInfo

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Load application configuration from environment variables."""

    database_url: str = "sqlite:///./pricing.db"
    admin_email: str = "admin@nicer.homes"
    admin_password: str = "change-me"
    session_secret: str = "development-only-change-me"
    hostex_access_token: str = ""
    hostex_base_url: str = "https://api.hostex.io"
    cookie_secure: bool = False
    business_timezone: str = "Asia/Makassar"
    scraper_adapter: str = "playwright"
    competitor_scrape_lambda_name: str = ""
    competitor_scrape_max_days: int = 30
    competitor_observation_fresh_hours: int = 24
    competitor_rough_fresh_days: int = 31
    competitor_precise_horizon_days: int = 60
    competitor_scrape_retention_days: int = Field(default=90, ge=1)
    competitor_quote_batch_size: int = Field(default=8, ge=1, le=8)
    competitor_quote_adults: int = 4
    competitor_callback_token: str = ""
    aws_region: str = "us-east-1"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def timezone(self) -> ZoneInfo:
        """Return the configured business timezone."""

        return ZoneInfo(self.business_timezone)


@lru_cache
def get_settings() -> Settings:
    """Return the cached process-wide settings object."""

    return Settings()
