import os
from functools import lru_cache


class Settings:
    app_name: str = "SupportOps AI Diagnostic API"
    app_description: str = (
        "Backend service for IT support diagnostics, ticket workflows, "
        "and deployment-safe troubleshooting automation."
    )
    app_version: str = "1.2.0"

    allowed_origins: list[str]

    def __init__(self) -> None:
        origins = os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,https://it-support-diagnostic-portal.vercel.app",
        )

        self.allowed_origins = [
            origin.strip()
            for origin in origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
