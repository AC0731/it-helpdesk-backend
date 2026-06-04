from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import diagnostics, tickets
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
)

# CORS is restricted through environment configuration so production deployments
# only allow trusted frontend origins instead of exposing the API to every domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(diagnostics.router, prefix="/api", tags=["Diagnostics"])
app.include_router(tickets.router, prefix="/api", tags=["Tickets"])


@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "SupportOps AI Diagnostic API is running.",
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}
