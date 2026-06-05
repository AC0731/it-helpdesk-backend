from typing import Optional

from pydantic import BaseModel, Field


class DiagnosticRequest(BaseModel):
    target: str = Field(..., min_length=1, max_length=255, description="Domain or IP address to diagnose")


class TicketRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=120)
    target: str = Field(..., min_length=1, max_length=255)
    ping_data: str
    traceroute_data: str
    priority: Optional[str] = Field(default="medium", max_length=40)


class TicketStatusUpdate(BaseModel):
    status: str = Field(..., min_length=1, max_length=40)


class AiInsightRequest(BaseModel):
    target: str = Field(..., min_length=1, max_length=255)
    ping_data: str = Field(default="", max_length=8000)
    traceroute_data: str = Field(default="", max_length=8000)
    ports: dict[str, str] = Field(default_factory=dict)