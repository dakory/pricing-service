from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import router
from app.database import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Nicer Homes Dynamic Pricing", version="0.1.0", lifespan=lifespan)
app.include_router(router)


@app.get("/")
def root():
    return {"status": "ok", "service": "pricing-api"}


@app.get("/health")
def health():
    return {"health": "ok"}
