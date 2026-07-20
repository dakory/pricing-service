from __future__ import annotations

from functools import lru_cache
from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./pricing.db"
    admin_email: str = "admin@nicer.homes"
    admin_password: str = "change-me"
    session_secret: str = "development-only-change-me"
    hostex_access_token: str = ""
    hostex_base_url: str = "https://api.hostex.io"
    cookie_secure: bool = False
    business_timezone: str = "Asia/Makassar"
    scraper_adapter: str = "playwright"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def timezone(self) -> ZoneInfo:
        return ZoneInfo(self.business_timezone)


@lru_cache
def get_settings() -> Settings:
    return Settings()
