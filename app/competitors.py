from __future__ import annotations

import re

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import (
    CompetitorDateError,
    CompetitorListing,
    CompetitorObservation,
    CompetitorPriceTarget,
    CompetitorScrapeBatch,
    CompetitorStayQuote,
    PricingGroup,
)


def extract_external_listing_id(url: str) -> str:
    """Extract the Airbnb room identifier from a canonical listing URL."""

    match = re.search(r"/rooms/(\d+)", url)
    if not match:
        raise ValueError(f"Competitor URL has no numeric room ID: {url}")
    return match.group(1)


def sync_group_competitor_listings(
    db: Session, pricing_group: PricingGroup
) -> None:
    """Synchronize normalized competitor rows with a group's canonical URLs."""

    desired_urls = set(pricing_group.competitor_urls or [])
    current = {
        item.canonical_url: item
        for item in db.scalars(
            select(CompetitorListing).where(
                CompetitorListing.pricing_group_id == pricing_group.id
            )
        )
    }
    for url in desired_urls - current.keys():
        db.add(
            CompetitorListing(
                pricing_group_id=pricing_group.id,
                canonical_url=url,
                external_listing_id=extract_external_listing_id(url),
            )
        )
    for url in current.keys() - desired_urls:
        item = current[url]
        for model in (
            CompetitorStayQuote,
            CompetitorPriceTarget,
            CompetitorScrapeBatch,
            CompetitorDateError,
            CompetitorObservation,
        ):
            db.execute(
                delete(model).where(model.competitor_listing_id == item.id)
            )
        db.delete(item)
