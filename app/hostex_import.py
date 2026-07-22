from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.hostex import HostexClient, HostexError
from app.models import HostexCalendarDay, HostexListing, Property, Reservation


def first(item: dict, *keys: str, default=None):
    for key in keys:
        if item.get(key) is not None:
            return item[key]
    return default


def as_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def as_decimal(value: Any) -> Decimal | None:
    if isinstance(value, dict):
        value = first(value, "amount", "value")
    try:
        return Decimal(str(value)) if value is not None else None
    except (InvalidOperation, ValueError):
        return None


def as_date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value)[:10]) if value else None
    except ValueError:
        return None


def as_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def external_property_id(item: dict) -> int | None:
    value = first(item, "property_id", "propertyId")
    if value is None and isinstance(item.get("property"), dict):
        value = first(item["property"], "id", "property_id")
    return as_int(value)


def upsert_properties(db: Session, records: list[dict]) -> tuple[int, int]:
    created = updated = 0
    for record in records:
        external_id = as_int(first(record, "id", "property_id"))
        if external_id is None:
            raise HostexError("Hostex property is missing id")
        name = str(first(record, "name", "property_name", "title", default=f"Hostex property {external_id}"))
        item = db.scalar(select(Property).where(Property.hostex_property_id == external_id))
        if item:
            item.name = name
            updated += 1
        else:
            # Imported properties are deliberately inactive until bounds and rules are reviewed.
            db.add(
                Property(
                    name=name,
                    hostex_property_id=external_id,
                    hostex_listing_id=f"unmapped:{external_id}",
                    active=False,
                    base_price=1_000_000,
                    min_price=500_000,
                    max_price=2_000_000,
                    rounding_increment=50_000,
                    season_factors={},
                    weekday_factors={},
                    minimum_stay_rules={},
                    orphan_gap_rules={},
                    competitor_urls=[],
                )
            )
            created += 1
    db.flush()
    return created, updated


def property_channel_map(property_records: list[dict]) -> dict[tuple[str, str], int]:
    mapping = {}
    for record in property_records:
        property_id = as_int(first(record, "id", "property_id"))
        channels = record.get("channels")
        if property_id is None or not isinstance(channels, list):
            continue
        for channel in channels:
            if not isinstance(channel, dict):
                continue
            listing_id = first(channel, "listing_id", "listingId")
            channel_type = first(channel, "channel_type", "channelType")
            if listing_id is not None and channel_type is not None:
                mapping[(str(listing_id), str(channel_type))] = property_id
    return mapping


def upsert_listings(
    db: Session, records: list[dict], property_records: list[dict] | None = None
) -> tuple[int, int]:
    created = updated = 0
    properties = {item.hostex_property_id: item for item in db.scalars(select(Property)) if item.hostex_property_id}
    channel_map = property_channel_map(property_records or [])
    for record in records:
        listing_id = first(record, "listing_id", "listingId", "id")
        channel_type = first(record, "channel_type", "channelType", "channel")
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
            "channel_account_id": as_int(first(record, "channel_account_id", "channelAccountId")),
            "readonly": bool(first(record, "readonly", "read_only", default=False)),
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
    created = updated = skipped = 0
    properties = {item.hostex_property_id: item for item in db.scalars(select(Property)) if item.hostex_property_id}
    for record in records:
        prop = properties.get(external_property_id(record))
        reservation_id = first(record, "reservation_code", "reservation_id", "stay_code", "id")
        check_in = as_date(first(record, "check_in_date", "check_in", "arrival_date"))
        check_out = as_date(first(record, "check_out_date", "check_out", "departure_date"))
        if not prop or reservation_id is None or not check_in or not check_out:
            skipped += 1
            continue
        item = db.scalar(
            select(Reservation).where(Reservation.property_id == prop.id, Reservation.hostex_id == str(reservation_id))
        )
        values = {
            "check_in": check_in,
            "check_out": check_out,
            "booked_at": as_datetime(first(record, "booked_at", "created_at")),
            "status": str(first(record, "status", "reservation_status", default="accepted")),
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
    for record in records:
        listing_id = first(record, "listing_id", "listingId")
        channel_type = first(record, "channel_type", "channelType")
        nights = first(record, "calendar", "calendars", "dates", "days")
        if listing_id is not None and isinstance(nights, list):
            for night in nights:
                if isinstance(night, dict):
                    yield str(listing_id), str(channel_type or "booking_site"), night
        elif listing_id is not None and as_date(first(record, "date", "stay_date")):
            yield str(listing_id), str(channel_type or "booking_site"), record


def upsert_calendars(db: Session, records: list[dict]) -> tuple[int, int, int]:
    created = updated = skipped = 0
    listings = {
        (item.listing_id, item.channel_type): item for item in db.scalars(select(HostexListing))
    }
    for listing_id, channel_type, night in calendar_nights(records):
        stay_date = as_date(first(night, "date", "stay_date"))
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
            "price": as_decimal(first(night, "price", "nightly_price", "rate")),
            "inventory": as_int(first(night, "inventory", "available")),
            "minimum_stay": as_int(first(night, "minimum_stay", "min_stay", default=restrictions.get("min_stay"))),
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
    today = today or date.today()
    properties = await client.properties()
    property_counts = upsert_properties(db, properties)
    listings = await client.listings()
    listing_counts = upsert_listings(db, listings, properties)
    reservations = await client.reservations(today - timedelta(days=365), today + timedelta(days=365))
    reservation_counts = upsert_reservations(db, reservations)

    calendar_listings = [
        {
            "listing_id": str(first(item, "listing_id", "listingId", "id")),
            "channel_type": str(first(item, "channel_type", "channelType", "channel")),
        }
        for item in listings
        if first(item, "listing_id", "listingId", "id") is not None
        and first(item, "channel_type", "channelType", "channel") is not None
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
