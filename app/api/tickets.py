from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Ticket
from app.models.schemas import TicketRequest, TicketStatusUpdate

router = APIRouter()

ALLOWED_STATUSES = {"open", "in_progress", "resolved", "closed"}
ALLOWED_PRIORITIES = {"low", "medium", "high", "urgent"}


def build_ticket_number() -> str:
    return f"TKT-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"


def build_ticket_summary(ticket: TicketRequest) -> str:
    return (
        f"Diagnostic ticket created for {ticket.target}. "
        "Review reachability, route diagnostic output, and open port results "
        "before assigning next troubleshooting steps."
    )


def serialize_ticket(ticket: Ticket) -> dict:
    return {
        "id": ticket.id,
        "ticket_id": ticket.ticket_number,
        "user_id": ticket.user_id,
        "target": ticket.target,
        "status": ticket.status,
        "priority": ticket.priority,
        "summary": ticket.summary,
        "ping_data": ticket.ping_data,
        "traceroute_data": ticket.traceroute_data,
        "created_at": ticket.created_at.isoformat(),
        "updated_at": ticket.updated_at.isoformat(),
    }


@router.post("/ticket")
async def generate_ticket(
    ticket: TicketRequest,
    db: Session = Depends(get_db),
):
    priority = (ticket.priority or "medium").lower().strip()

    if priority not in ALLOWED_PRIORITIES:
        raise HTTPException(
            status_code=400,
            detail=f"Priority must be one of: {', '.join(sorted(ALLOWED_PRIORITIES))}.",
        )

    saved_ticket = Ticket(
        ticket_number=build_ticket_number(),
        user_id=ticket.user_id.strip(),
        target=ticket.target.strip(),
        status="open",
        priority=priority,
        summary=build_ticket_summary(ticket),
        ping_data=ticket.ping_data,
        traceroute_data=ticket.traceroute_data,
    )

    db.add(saved_ticket)
    db.commit()
    db.refresh(saved_ticket)

    return {
        "status": "success",
        "message": f"Ticket {saved_ticket.ticket_number} successfully created.",
        "ticket_id": saved_ticket.ticket_number,
        "data_logged": {
            "user": saved_ticket.user_id,
            "issue_target": saved_ticket.target,
        },
        "ticket": serialize_ticket(saved_ticket),
    }


@router.get("/tickets")
async def list_tickets(
    status: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Ticket)

    if status:
        normalized_status = status.lower().strip()

        if normalized_status not in ALLOWED_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Status must be one of: {', '.join(sorted(ALLOWED_STATUSES))}.",
            )

        query = query.filter(Ticket.status == normalized_status)

    tickets = query.order_by(Ticket.created_at.desc()).limit(limit).all()

    return {
        "count": len(tickets),
        "tickets": [serialize_ticket(ticket) for ticket in tickets],
    }


@router.get("/tickets/{ticket_id}")
async def get_ticket(
    ticket_id: str,
    db: Session = Depends(get_db),
):
    ticket = db.query(Ticket).filter(Ticket.ticket_number == ticket_id).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")

    return serialize_ticket(ticket)


@router.patch("/tickets/{ticket_id}")
async def update_ticket_status(
    ticket_id: str,
    payload: TicketStatusUpdate,
    db: Session = Depends(get_db),
):
    new_status = payload.status.lower().strip()

    if new_status not in ALLOWED_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Status must be one of: {', '.join(sorted(ALLOWED_STATUSES))}.",
        )

    ticket = db.query(Ticket).filter(Ticket.ticket_number == ticket_id).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")

    ticket.status = new_status

    db.commit()
    db.refresh(ticket)

    return {
        "status": "success",
        "message": f"Ticket {ticket.ticket_number} updated to {ticket.status}.",
        "ticket": serialize_ticket(ticket),
    }
