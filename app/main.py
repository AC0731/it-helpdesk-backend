import logging
import re
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api import ai, diagnostics, tickets
from app.core.config import get_settings
from app.db.database import engine, init_db

settings = get_settings()
request_logger = logging.getLogger("supportops.request")
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")


def normalize_request_id(value: str | None) -> str:
    if value and REQUEST_ID_PATTERN.fullmatch(value):
        return value
    return uuid4().hex


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_operational_headers(request: Request, call_next):
    request_id = normalize_request_id(request.headers.get("x-request-id"))
    started = perf_counter()

    response = await call_next(request)

    elapsed_ms = round((perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = str(elapsed_ms)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"

    request_logger.info(
        "request_completed method=%s path=%s status=%s request_id=%s duration_ms=%s",
        request.method,
        request.url.path,
        response.status_code,
        request_id,
        elapsed_ms,
    )
    return response


app.include_router(diagnostics.router, prefix="/api", tags=["Diagnostics"])
app.include_router(tickets.router, prefix="/api", tags=["Tickets"])
app.include_router(ai.router, prefix="/api", tags=["AI Insights"])


@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "SupportOps AI Diagnostic API is running.",
    }


@app.get("/health")
@app.get("/health/live")
async def health_check():
    return {"status": "ok"}


@app.get("/health/ready")
async def readiness_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        request_logger.exception("database_readiness_failed")
        raise HTTPException(
            status_code=503,
            detail="Database readiness check failed.",
        ) from exc

    return {
        "status": "ready",
        "database": "ok",
    }
