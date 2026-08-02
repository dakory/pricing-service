from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

import httpx


class HostexError(RuntimeError):
    """Represent a transport or body-level Hostex API failure."""

    def __init__(self, message: str, *, code: int | str | None = None, retry_after: float | None = None):
        """Capture the Hostex code and optional retry delay."""

        super().__init__(message)
        self.code = code
        self.retry_after = retry_after

    @property
    def retryable(self) -> bool:
        """Return whether Hostex identified the failure as rate limiting."""

        return str(self.code) == "429"


@dataclass
class PublishResult:
    """Summarize one accepted Hostex price publication request."""

    accepted: int
    response: dict


def response_items(body: Any, resource: str) -> list[dict]:
    """Extract Hostex collections while preserving strict item validation."""
    if isinstance(body, list):
        items = body
    elif isinstance(body, dict):
        value = body.get(resource)
        if value is None and isinstance(body.get("data"), dict):
            value = body["data"].get(resource)
            if value is None:
                value = body["data"].get("items")
        if value is None:
            value = body.get("data") or body.get("items") or body.get("result")
        items = value
    else:
        items = None
    if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
        if isinstance(body, dict):
            shape = {key: type(value).__name__ for key, value in body.items()}
            nested = {
                key: list(value.keys())
                for key, value in body.items()
                if isinstance(value, dict)
            }
        else:
            shape, nested = type(body).__name__, {}
        raise HostexError(
            f"Hostex {resource} response has an unsupported shape: top={shape}, nested_keys={nested}"
        )
    return items


class HostexClient:
    """Hostex v3 boundary with body-error detection and bounded retries."""

    def __init__(
        self,
        token: str,
        base_url: str = "https://api.hostex.io",
        *,
        client: httpx.AsyncClient | None = None,
        max_attempts: int = 3,
    ):
        """Create an authenticated Hostex client or wrap a supplied test client."""

        if not token:
            raise ValueError("Hostex access token is required")
        self.max_attempts = max_attempts
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Hostex-Access-Token": token,
                "User-Agent": "NicerHomesPricing/0.1 (admin@nicer.homes)",
                "Accept": "application/json",
            },
            timeout=30,
        )
        if client is not None:
            self.client.headers.update(
                {
                    "Hostex-Access-Token": token,
                    "User-Agent": "NicerHomesPricing/0.1 (admin@nicer.homes)",
                    "Accept": "application/json",
                }
            )

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        """Send one request with bounded retries and body-error validation."""

        last_error: Exception | None = None
        for attempt in range(self.max_attempts):
            try:
                response = await self.client.request(method, path, **kwargs)
                response.raise_for_status()
                body = response.json()
                if not isinstance(body, dict):
                    raise HostexError("Hostex response is not a JSON object")
                code = body.get("error_code", body.get("code"))
                if code not in (None, 0, "0", 200, "200", "success"):
                    retry_after = float(response.headers.get("Retry-After", 0) or 0)
                    raise HostexError(
                        f"Hostex error {code}: {body.get('error_msg') or body.get('message') or 'unknown'}",
                        code=code,
                        retry_after=retry_after,
                    )
                if body.get("success") is False:
                    raise HostexError(f"Hostex rejected request: {body.get('message', 'unknown')}")
                return body
            except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError, HostexError) as exc:
                last_error = exc
                retryable = isinstance(exc, (httpx.TimeoutException, httpx.TransportError))
                retryable = retryable or (isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429)
                retryable = retryable or (isinstance(exc, HostexError) and exc.retryable)
                if not retryable or attempt + 1 == self.max_attempts:
                    raise
                base = exc.retry_after if isinstance(exc, HostexError) and exc.retry_after else 2**attempt
                await asyncio.sleep(base * random.uniform(0.75, 1.25))
        raise last_error  # pragma: no cover

    async def _all_pages(self, path: str, resource: str, **params) -> list[dict]:
        """Retrieve every offset-based page for a Hostex collection."""

        offset, limit, collected = 0, 100, []
        while True:
            body = await self._request("GET", path, params={**params, "offset": offset, "limit": limit})
            page = response_items(body, resource)
            collected.extend(page)
            if len(page) < limit:
                return collected
            offset += limit

    async def properties(self) -> list[dict]:
        """Return all Hostex properties."""

        return await self._all_pages("/v3/properties", "properties")

    async def listings(self) -> list[dict]:
        """Return all connected channel listings."""

        return await self._all_pages("/v3/listings", "listings")

    async def reservations(self, start_date: date, end_date: date) -> list[dict]:
        """Return deduplicated reservations across valid 180-day windows."""

        records: list[dict] = []
        window_start = start_date
        while window_start <= end_date:
            window_end = min(window_start + timedelta(days=179), end_date)
            records.extend(
                await self._all_pages(
                    "/v3/reservations",
                    "reservations",
                    start_check_in_date=window_start.isoformat(),
                    end_check_in_date=window_end.isoformat(),
                    order_by="created_at",
                )
            )
            window_start = window_end + timedelta(days=1)
        unique = {}
        for record in records:
            key = record.get("reservation_code") or record.get("stay_code") or record.get("id")
            if key is None:
                key = repr(sorted(record.items()))
            unique[str(key)] = record
        return list(unique.values())

    async def pricing_ratios(self, property_id: int) -> list[dict]:
        """Return channel pricing ratios for one Hostex property."""

        body = await self._request("GET", "/v3/pricing_ratios", params={"property_id": property_id})
        if isinstance(body.get("data"), dict) and isinstance(body["data"].get("channels"), list):
            return body["data"]["channels"]
        return response_items(body, "pricing_ratios")

    async def calendars(self, listings: list[dict], start_date: date, end_date: date) -> list[dict]:
        """Return calendar data for a batch of channel listings."""

        body = await self._request(
            "POST",
            "/v3/listings/calendar",
            json={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "listings": listings,
            },
        )
        try:
            return response_items(body, "calendars")
        except HostexError:
            # The live v3 envelope names this collection `data.listings`.
            return response_items(body, "listings")

    async def publish_prices(
        self,
        listing_id: str,
        entries: list[dict],
        channel_type: str = "booking_site",
    ) -> PublishResult:
        """Submit a batch of daily prices for one channel listing."""

        body = await self._request(
            "POST",
            "/v3/listings/prices",
            json={
                "listing_id": listing_id,
                "channel_type": channel_type,
                "prices": entries,
            },
        )
        return PublishResult(accepted=len(entries), response=body)

    async def calendar(self, listing_id: str, start: str, end: str, channel_type: str = "booking_site") -> dict:
        """Return raw calendar data for one listing and date range."""

        body = await self._request(
            "POST",
            "/v3/listings/calendar",
            json={
                "start_date": start,
                "end_date": end,
                "listings": [{"listing_id": listing_id, "channel_type": channel_type}],
            },
        )
        return body

    async def close(self):
        """Close the internally owned HTTP client."""

        if self._owns_client:
            await self.client.aclose()
