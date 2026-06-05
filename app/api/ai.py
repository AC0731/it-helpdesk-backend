import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import AiInsight, Ticket
from app.models.schemas import AiInsightRequest, SavedAiInsightRequest
from app.services.ai_insights import build_ai_insight
from app.services.target_validation import TargetValidationError, validate_public_target

router = APIRouter()


def serialize_ai_insight(insight: AiInsight) -> dict:
    return {
        "id": insight.id,
        "ticket_id": insight.ticket_number,
        "target": insight.target,
        "provider": insight.provider,
        "risk_level": insight.risk_level,
        "summary": insight.summary,
        "probable_causes": json.loads(insight.probable_causes_json),
        "recommended_next_steps": json.loads(insight.recommended_next_steps_json),
        "created_at": insight.created_at.isoformat(),
    }


@router.post("/ai/insight")
async def generate_ai_insight(payload: AiInsightRequest):
    insight = await build_ai_insight(payload)

    return {
        "target": payload.target,
        "insight": insight,
    }


@router.post("/ai/insight/save")
async def save_ai_insight(
    payload: SavedAiInsightRequest,
    db: Session = Depends(get_db),
):
    try:
        target = validate_public_target(payload.target)
    except TargetValidationError as error:
        raise HTTPException(status_code=400, detail=str(error))

    ticket_number = payload.ticket_id.strip() if payload.ticket_id else None

    if ticket_number:
      ticket = db.query(Ticket).filter(Ticket.ticket_number == ticket_number).first()

      if not ticket:
          raise HTTPException(status_code=404, detail="Ticket not found.")

    normalized_payload = AiInsightRequest(
        target=target,
        ping_data=payload.ping_data,
        traceroute_data=payload.traceroute_data,
        ports=payload.ports,
    )

    generated_insight = await build_ai_insight(normalized_payload)

    saved_insight = AiInsight(
        ticket_number=ticket_number,
        target=target,
        provider=generated_insight.get("provider", "unknown"),
        risk_level=generated_insight.get("risk_level", "medium"),
        summary=generated_insight.get("summary", ""),
        probable_causes_json=json.dumps(generated_insight.get("probable_causes", [])),
        recommended_next_steps_json=json.dumps(generated_insight.get("recommended_next_steps", [])),
    )

    db.add(saved_insight)
    db.commit()
    db.refresh(saved_insight)

    return {
        "status": "success",
        "message": "AI insight saved.",
        "insight": serialize_ai_insight(saved_insight),
    }


@router.get("/ai/insights")
async def list_ai_insights(
    ticket_id: str | None = None,
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(AiInsight)

    if ticket_id:
        query = query.filter(AiInsight.ticket_number == ticket_id.strip())

    insights = query.order_by(AiInsight.created_at.desc()).limit(limit).all()

    return {
        "count": len(insights),
        "insights": [serialize_ai_insight(insight) for insight in insights],
    }