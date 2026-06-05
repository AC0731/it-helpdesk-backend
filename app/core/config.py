import os
from functools import lru_cache


class Settings:
    app_name: str = "SupportOps AI Diagnostic API"
    app_description: str = (
        "Backend service for IT support diagnostics, ticket workflows, "
        "and deployment-safe AI troubleshooting automation."
    )
    app_version: str = "1.4.0"

    allowed_origins: list[str]
    database_url: str
    openai_api_key: str
    ai_model: str

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

        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./supportops.db")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.ai_model = os.getenv("AI_MODEL", "gpt-5.5").strip()


@lru_cache
def get_settings() -> Settings:
    return Settings()