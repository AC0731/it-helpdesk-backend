from fastapi import APIRouter

from app.models.schemas import AiInsightRequest
from app.services.ai_insights import build_ai_insight

router = APIRouter()


@router.post("/ai/insight")
async def generate_ai_insight(payload: AiInsightRequest):
    insight = await build_ai_insight(payload)

    return {
        "target": payload.target,
        "insight": insight,
    }