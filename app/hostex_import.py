from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.hostex import HostexClient, HostexError
from app.models import HostexCalendarDay, HostexListing, PricingGroup, Property, Reservation


def first_present_value(item: dict, *keys: str, default=None):
    """Return the first non-null value among alternate Hostex field names."""

    for key in keys:
        if item.get(key) is not None:
            return item[key]
    return default


def parse_integer(value: Any) -> int | None:
    """Parse an optional integer without raising on malformed API data."""

    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def parse_decimal(value: Any) -> Decimal | None:
    """Parse an optional decimal from a scalar or amount wrapper."""

    if isinstance(value, dict):
        value = first_present_value(value, "amount", "value")
    try:
        return Decimal(str(value)) if value is not None else None
    except (InvalidOperation, ValueError):
        return None


def parse_date(value: Any) -> date | None:
    """Parse an ISO date while tolerating a trailing timestamp."""

    try:
        return date.fromisoformat(str(value)[:10]) if value else None
    except ValueError:
        return None


def parse_datetime(value: Any) -> datetime | None:
    """Parse an ISO timestamp and normalize missing timezone data to UTC."""

    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def external_property_id(item: dict) -> int | None:
    """Extract a Hostex property identifier from supported response shapes."""

    value = first_present_value(item, "property_id", "propertyId")
    if value is None and isinstance(item.get("property"), dict):
        value = first_present_value(item["property"], "id", "property_id")
    return parse_integer(value)


def upsert_properties(db: Session, records: list[dict]) -> tuple[int, int]:
    """Create or refresh local property mappings from Hostex records."""

    default_group = db.scalar(
        select(PricingGroup).order_by(PricingGroup.id).limit(1)
    )
    if not default_group:
        default_group = PricingGroup(
            name="Default pricing group",
            pricing_settings={},
            competitor_urls=[],
        )
        db.add(default_group)
        db.flush()
    created = updated = 0
    for record in records:
        external_id = parse_integer(first_present_value(record, "id", "property_id"))
        if external_id is None:
            raise HostexError("Hostex property is missing id")
        name = str(first_present_value(record, "name", "property_name", "title", default=f"Hostex property {external_id}"))
        cover = record.get("cover") if isinstance(record.get("cover"), dict) else {}
        thumbnail_url = first_present_value(cover, "small_url", "large_url", "original_url")
        item = db.scalar(select(Property).where(Property.hostex_property_id == external_id))
        if item:
            item.name = name
            item.thumbnail_url = thumbnail_url
            updated += 1
        else:
            # Imported properties are deliberately inactive until bounds and rules are reviewed.
            db.add(
                Property(
                    name=name,
                    pricing_group_id=default_group.id,
                    hostex_property_id=external_id,
                    thumbnail_url=thumbnail_url,
                    hostex_listing_id=f"unmapped:{external_id}",
                    active=False,
                    min_price=500_000,
                    max_price=2_000_000,
                    rounding_increment=50_000,
                    pricing_settings={},
                )
            )
            created += 1
    db.flush()
    return created, updated


def property_channel_map(property_records: list[dict]) -> dict[tuple[str, str], int]:
    """Map channel listing identifiers to their Hostex property identifiers."""

    mapping = {}
    for record in property_records:
        property_id = parse_integer(first_present_value(record, "id", "property_id"))
        channels = record.get("channels")
        if property_id is None or not isinstance(channels, list):
            continue
        for channel in channels:
            if not isinstance(channel, dict):
                continue
            listing_id = first_present_value(channel, "listing_id", "listingId")
            channel_type = first_present_value(channel, "channel_type", "channelType")
            if listing_id is not None and channel_type is not None:
                mapping[(str(listing_id), str(channel_type))] = property_id
    return mapping


def upsert_listings(
    db: Session, records: list[dict], property_records: list[dict] | None = None
) -> tuple[int, int]:
    """Create or refresh channel listings and link them to properties."""

    created = updated = 0
    properties = {item.hostex_property_id: item for item in db.scalars(select(Property)) if item.hostex_property_id}
    channel_map = property_channel_map(property_records or [])
    for record in records:
        listing_id = first_present_value(record, "listing_id", "listingId", "id")
        channel_type = first_present_value(record, "channel_type", "channelType", "channel")
        if listing_id is None or channel_type is None:
            raise HostexError("Hostex listing is missing listing_id or channel_type")
        listing_id, channel_type = str(listing_id), str(channel_type)
        ext_property_id = external_property_id(record) or channel_map.get((listing_id, channel_type))
        prop = properties.get(ext_property_id)
        item = db.scalar(
            select(HostexListing).where(
                HostexListing.listing_id == listing_id, HostexListing.channel_type == channel_type
            )
        )
        values = {
            "property_id": prop.id if prop else None,
            "hostex_property_id": ext_property_id,
            "channel_account_id": parse_integer(first_present_value(record, "channel_account_id", "channelAccountId")),
            "readonly": bool(first_present_value(record, "readonly", "read_only", default=False)),
            "raw": record,
            "imported_at": datetime.now(timezone.utc),
        }
        if item:
            for key, value in values.items():
                setattr(item, key, value)
            updated += 1
        else:
            db.add(HostexListing(listing_id=listing_id, channel_type=channel_type, **values))
            created += 1
        if prop and channel_type == "booking_site":
            prop.booking_site_listing_id = listing_id
            prop.hostex_listing_id = listing_id
    db.flush()
    return created, updated


def upsert_reservations(db: Session, records: list[dict]) -> tuple[int, int, int]:
    """Create or refresh reservations while reporting unmappable records."""

    created = updated = skipped = 0
    properties = {item.hostex_property_id: item for item in db.scalars(select(Property)) if item.hostex_property_id}
    for record in records:
        prop = properties.get(external_property_id(record))
        reservation_id = first_present_value(record, "reservation_code", "reservation_id", "stay_code", "id")
        check_in = parse_date(first_present_value(record, "check_in_date", "check_in", "arrival_date"))
        check_out = parse_date(first_present_value(record, "check_out_date", "check_out", "departure_date"))
        if not prop or reservation_id is None or not check_in or not check_out:
            skipped += 1
            continue
        item = db.scalar(
            select(Reservation).where(Reservation.property_id == prop.id, Reservation.hostex_id == str(reservation_id))
        )
        values = {
            "check_in": check_in,
            "check_out": check_out,
            "booked_at": parse_datetime(first_present_value(record, "booked_at", "created_at")),
            "status": str(first_present_value(record, "status", "reservation_status", default="accepted")),
        }
        if item:
            for key, value in values.items():
                setattr(item, key, value)
            updated += 1
        else:
            db.add(Reservation(property_id=prop.id, hostex_id=str(reservation_id), **values))
            created += 1
    db.flush()
    return created, updated, skipped


def calendar_nights(records: list[dict]) -> Iterable[tuple[str, str, dict]]:
    """Flatten supported Hostex calendar envelopes into listing-day tuples."""

    for record in records:
        listing_id = first_present_value(record, "listing_id", "listingId")
        channel_type = first_present_value(record, "channel_type", "channelType")
        nights = first_present_value(record, "calendar", "calendars", "dates", "days")
        if listing_id is not None and isinstance(nights, list):
            for night in nights:
                if isinstance(night, dict):
                    yield str(listing_id), str(channel_type or "booking_site"), night
        elif listing_id is not None and parse_date(first_present_value(record, "date", "stay_date")):
            yield str(listing_id), str(channel_type or "booking_site"), record


def upsert_calendars(db: Session, records: list[dict]) -> tuple[int, int, int]:
    """Create or refresh imported listing calendar days."""

    created = updated = skipped = 0
    listings = {
        (item.listing_id, item.channel_type): item for item in db.scalars(select(HostexListing))
    }
    for listing_id, channel_type, night in calendar_nights(records):
        stay_date = parse_date(first_present_value(night, "date", "stay_date"))
        if not stay_date:
            skipped += 1
            continue
        listing = listings.get((listing_id, channel_type))
        item = db.scalar(
            select(HostexCalendarDay).where(
                HostexCalendarDay.listing_id == listing_id,
                HostexCalendarDay.channel_type == channel_type,
                HostexCalendarDay.stay_date == stay_date,
            )
        )
        restrictions = night.get("restrictions") if isinstance(night.get("restrictions"), dict) else {}
        values = {
            "property_id": listing.property_id if listing else None,
            "price": parse_decimal(first_present_value(night, "price", "nightly_price", "rate")),
            "inventory": parse_integer(first_present_value(night, "inventory", "available")),
            "minimum_stay": parse_integer(first_present_value(night, "minimum_stay", "min_stay", default=restrictions.get("min_stay"))),
            "raw": night,
            "imported_at": datetime.now(timezone.utc),
        }
        if item:
            for key, value in values.items():
                setattr(item, key, value)
            updated += 1
        else:
            db.add(
                HostexCalendarDay(
                    listing_id=listing_id,
                    channel_type=channel_type,
                    stay_date=stay_date,
                    **values,
                )
            )
            created += 1
    db.flush()
    return created, updated, skipped


async def import_hostex(db: Session, client: HostexClient, *, today: date | None = None) -> dict:
    """Import and atomically persist read-only Hostex portfolio data."""

    today = today or date.today()
    properties = await client.properties()
    property_counts = upsert_properties(db, properties)
    listings = await client.listings()
    listing_counts = upsert_listings(db, listings, properties)
    reservations = await client.reservations(today - timedelta(days=365), today + timedelta(days=365))
    reservation_counts = upsert_reservations(db, reservations)

    calendar_listings = [
        {
            "listing_id": str(first_present_value(item, "listing_id", "listingId", "id")),
            "channel_type": str(first_present_value(item, "channel_type", "channelType", "channel")),
        }
        for item in listings
        if first_present_value(item, "listing_id", "listingId", "id") is not None
        and first_present_value(item, "channel_type", "channelType", "channel") is not None
    ]
    calendar_records = []
    for start in range(0, len(calendar_listings), 20):
        calendar_records.extend(
            await client.calendars(calendar_listings[start : start + 20], today, today + timedelta(days=365))
        )
    calendar_counts = upsert_calendars(db, calendar_records)
    db.commit()
    return {
        "properties": {"created": property_counts[0], "updated": property_counts[1], "received": len(properties)},
        "listings": {"created": listing_counts[0], "updated": listing_counts[1], "received": len(listings)},
        "reservations": {
            "created": reservation_counts[0], "updated": reservation_counts[1], "skipped": reservation_counts[2],
            "received": len(reservations),
        },
        "calendar": {
            "created": calendar_counts[0], "updated": calendar_counts[1], "skipped": calendar_counts[2],
            "received": sum(1 for _ in calendar_nights(calendar_records)),
        },
    }


async def import_booking_site_calendars(
    db: Session,
    client: HostexClient,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    """Refresh only active BookingSite calendars without a full Hostex import."""

    start_date = start_date or date.today()
    end_date = end_date or start_date + timedelta(days=365)
    if end_date < start_date:
        raise ValueError("end_date must not precede start_date")

    rows = db.scalars(
        select(HostexListing)
        .join(Property, HostexListing.property_id == Property.id)
        .where(
            HostexListing.channel_type == "booking_site",
            Property.active.is_(True),
        )
        .order_by(HostexListing.listing_id)
    ).all()
    listings = [
        {"listing_id": row.listing_id, "channel_type": row.channel_type}
        for row in rows
    ]
    calendar_records: list[dict] = []
    for offset in range(0, len(listings), 20):
        calendar_records.extend(
            await client.calendars(listings[offset : offset + 20], start_date, end_date)
        )
    counts = upsert_calendars(db, calendar_records)
    db.commit()
    return {
        "scope": "booking_site",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "listings": len(listings),
        "calendar": {
            "created": counts[0],
            "updated": counts[1],
            "skipped": counts[2],
            "received": sum(1 for _ in calendar_nights(calendar_records)),
        },
    }
