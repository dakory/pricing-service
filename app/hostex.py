from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx


class HostexError(RuntimeError):
    pass


@dataclass
class PublishResult:
    accepted: int
    response: dict


class HostexClient:
    """Hostex boundary. All body-level errors are treated as failures."""

    def __init__(self, token: str, base_url: str = "https://api.hostex.io"):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Hostex-Access-Token": token},
            timeout=30,
        )

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        response = await self.client.request(method, path, **kwargs)
        response.raise_for_status()
        body = response.json()
        code = body.get("code")
        if code and str(code) not in {"0", "200", "success"}:
            raise HostexError(f"Hostex body error {code}: {body.get('message', 'unknown')}")
        if body.get("success") is False:
            raise HostexError(f"Hostex rejected request: {body.get('message', 'unknown')}")
        return body

    async def publish_prices(self, listing_id: str, entries: list[dict]) -> PublishResult:
        last_error = None
        for attempt in range(3):
            try:
                body = await self._request(
                    "POST", "/v3/listings/prices", json={"listingId": listing_id, "prices": entries}
                )
                return PublishResult(accepted=len(entries), response=body)
            except (httpx.HTTPStatusError, HostexError) as exc:
                last_error = exc
                retryable = isinstance(exc, HostexError) and "429" in str(exc)
                retryable = retryable or (
                    isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429
                )
                if not retryable or attempt == 2:
                    raise
                await asyncio.sleep(2**attempt)
        raise last_error  # pragma: no cover

    async def calendar(self, listing_id: str, start: str, end: str) -> dict:
        return await self._request(
            "GET", "/v3/listings/calendar", params={"listingId": listing_id, "startDate": start, "endDate": end}
        )

    async def close(self):
        await self.client.aclose()
