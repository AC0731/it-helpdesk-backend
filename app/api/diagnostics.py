import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import DiagnosticRun
from app.models.schemas import DiagnosticRequest
from app.services.network_tools import run_ping, run_port_scan, run_traceroute

router = APIRouter()


def serialize_diagnostic_run(run: DiagnosticRun) -> dict:
    try:
        ports = json.loads(run.port_results_json)
    except json.JSONDecodeError:
        ports = {}

    return {
        "id": run.id,
        "timestamp": run.created_at.isoformat(),
        "target": run.target,
        "results": {
            "ping": run.ping_result,
            "traceroute": run.traceroute_result,
            "ports": ports,
        },
    }


@router.post("/diagnostics")
async def execute_diagnostics(
    req: DiagnosticRequest,
    db: Session = Depends(get_db),
):
    target = req.target.strip()

    if not target:
        raise HTTPException(status_code=400, detail="Target IP or domain is required.")

    ping_result = run_ping(target).strip()
    trace_result = run_traceroute(target).strip()
    port_result = run_port_scan(target)

    diagnostic_run = DiagnosticRun(
        target=target,
        ping_result=ping_result,
        traceroute_result=trace_result,
        port_results_json=json.dumps(port_result),
    )

    db.add(diagnostic_run)
    db.commit()
    db.refresh(diagnostic_run)

    return {
        "diagnostic_id": diagnostic_run.id,
        "timestamp": datetime.now().isoformat(),
        "target": target,
        "results": {
            "ping": ping_result,
            "traceroute": trace_result,
            "ports": port_result,
        },
    }


@router.get("/diagnostics/history")
async def list_diagnostic_history(
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    runs = (
        db.query(DiagnosticRun)
        .order_by(DiagnosticRun.created_at.desc())
        .limit(limit)
        .all()
    )

    return {
        "count": len(runs),
        "diagnostics": [serialize_diagnostic_run(run) for run in runs],
    }
