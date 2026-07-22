import asyncio
import json

from app.config import get_settings
from app.database import SessionLocal
from app.hostex import HostexClient
from app.hostex_import import import_hostex


async def main():
    settings = get_settings()
    if not settings.hostex_access_token:
        raise SystemExit("HOSTEX_ACCESS_TOKEN is not configured")
    client = HostexClient(settings.hostex_access_token, settings.hostex_base_url)
    try:
        with SessionLocal() as db:
            summary = await import_hostex(db, client)
            print(json.dumps(summary, indent=2))
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
