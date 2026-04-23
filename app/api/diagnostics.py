from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.models.schemas import DiagnosticRequest
from app.services.network_tools import run_ping, run_traceroute

router = APIRouter()

@router.post("/diagnostics")
async def execute_diagnostics(req: DiagnosticRequest):
    target = req.target
    if not target:
        raise HTTPException(status_code=400, detail="Target IP or domain is required.")

    ping_result = run_ping(target)
    trace_result = run_traceroute(target)

    return {
        "timestamp": datetime.now().isoformat(),
        "target": target,
        "results": {
            "ping": ping_result.strip(),
            "traceroute": trace_result.strip()
        }
    }