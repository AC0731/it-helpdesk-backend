from fastapi import APIRouter
from datetime import datetime
from app.models.schemas import TicketRequest

router = APIRouter()

@router.post("/ticket")
async def generate_mock_ticket(ticket: TicketRequest):
    ticket_id = f"TKT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return {
        "status": "success",
        "message": f"Ticket {ticket_id} successfully created.",
        "ticket_id": ticket_id,
        "data_logged": {
            "user": ticket.user_id,
            "issue_target": ticket.target
        }
    }