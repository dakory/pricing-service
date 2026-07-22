from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime


class StructuralChangeError(RuntimeError):
    """Raised before persisting any observations when a page no longer matches."""


@dataclass(frozen=True)
class ScrapedNight:
    """Represent one parsed competitor calendar night."""

    stay_date: date
    price: int | None
    available: bool
    currency: str
    scraped_at: datetime
    parser_version: str


class CompetitorAdapter(ABC):
    """Define the replaceable competitor-collection interface."""

    @abstractmethod
    async def collect(self, url: str) -> list[ScrapedNight]:
        """Collect dated prices and availability from a competitor URL."""

        raise NotImplementedError


class PlaywrightAirbnbAdapter(CompetitorAdapter):
    """Collect Airbnb calendar payloads through a single browser context."""

    # Increment when the accepted Airbnb payload structure changes.
    parser_version = "airbnb-v1"

    async def collect(self, url: str) -> list[ScrapedNight]:
        """Load an Airbnb page and fail closed on unknown payload structures."""

        # Browser execution lives in the dedicated scraper image. Keeping this
        # boundary small allows replacement with a managed provider.
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise RuntimeError("Playwright is only installed in the scraper image") from exc
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(locale="en-US")
            page = await context.new_page()
            await page.goto(url, wait_until="networkidle")
            payload = await page.locator("#data-deferred-state-0").text_content()
            await browser.close()
        if not payload or "calendar" not in payload.lower():
            raise StructuralChangeError("Airbnb calendar payload not found")
        # Airbnb's private payload changes frequently. The parser is intentionally
        # fail-closed: a versioned fixture parser must be added for the observed shape.
        raise StructuralChangeError("Unsupported Airbnb payload shape for parser airbnb-v1")
