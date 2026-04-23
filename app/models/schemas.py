from pydantic import BaseModel

class DiagnosticRequest(BaseModel):
    target: str

class TicketRequest(BaseModel):
    user_id: str
    target: str
    ping_data: str
    traceroute_data: str