from contextlib import asynccontextmanager
import os

from fastapi import FastAPI

from app.api import router
@asynccontextmanager
async def lifespan(_: FastAPI):
    """Provide the application lifespan hook for future startup resources."""

    yield


app = FastAPI(title="Nicer Homes Dynamic Pricing", version="0.1.0", lifespan=lifespan)
app.include_router(router)


@app.get("/")
def root():
    """Return basic service identity and availability."""

    return {"status": "ok", "service": "pricing-api"}


@app.get("/health")
def health():
    """Return the lightweight container health response."""

    return {"health": "ok"}


@app.get("/version")
def version():
    """Expose the release identifier used by deployment smoke tests."""

    return {
        "service": "pricing-api",
        "version": app.version,
        "commit": os.getenv("BUILD_SHA", "dev"),
    }
