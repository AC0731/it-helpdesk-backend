from pydantic import BaseModel, Field


class DiagnosticRequest(BaseModel):
    target: str = Field(..., min_length=1, description="Domain or IP address to diagnose")


class TicketRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    target: str = Field(..., min_length=1)
    ping_data: str
    traceroute_data: str
