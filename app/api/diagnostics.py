import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from threading import BoundedSemaphore

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.database import get_db
from app.db.models import DiagnosticRun
from app.models.schemas import DiagnosticRequest
from app.services.network_tools import (
    NetworkTargetError,
    resolve_public_target_ip,
    run_diagnostic_bundle,
)
from app.services.target_validation import TargetValidationError, validate_public_target

router = APIRouter()
settings = get_settings()
diagnostic_logger = logging.getLogger("supportops.diagnostics")

_DIAGNOSTIC_EXECUTOR = ThreadPoolExecutor(
    max_workers=settings.diagnostic_max_concurrency,
    thread_name_prefix="supportops-diagnostic",
)
_DIAGNOSTIC_CAPACITY = BoundedSemaphore(settings.diagnostic_max_concurrency)


class DiagnosticCapacityError(RuntimeError):
    pass


class DiagnosticTimeoutError(TimeoutError):
    pass


def log_diagnostic_event(level: int, event: str, **fields) -> None:
    diagnostic_logger.log(
        level,
        json.dumps(
            {
                "event": event,
                **fields,
            },
            default=str,
            sort_keys=True,
        ),
    )


async def execute_bounded_diagnostic(resolved_ip: str) -> dict:
    if not _DIAGNOSTIC_CAPACITY.acquire(blocking=False):
        raise DiagnosticCapacityError("Diagnostic capacity is currently exhausted.")

    loop = asyncio.get_running_loop()
    future = loop.run_in_executor(
        _DIAGNOSTIC_EXECUTOR,
        run_diagnostic_bundle,
        resolved_ip,
    )
    release_in_finally = True

    try:
        return await asyncio.wait_for(
            asyncio.shield(future),
            timeout=settings.diagnostic_timeout_seconds,
        )
    except TimeoutError as exc:
        # The worker cannot be force-killed safely. Keep its capacity slot until
        # the bounded worker actually exits so timed-out jobs cannot create an
        # unbounded execution queue.
        release_in_finally = False
        future.add_done_callback(lambda _future: _DIAGNOSTIC_CAPACITY.release())
        raise DiagnosticTimeoutError(
            f"Diagnostic execution exceeded {settings.diagnostic_timeout_seconds:g} seconds."
        ) from exc
    finally:
        if release_in_finally:
            _DIAGNOSTIC_CAPACITY.release()


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
    request: Request,
    db: Session = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", "unknown")

    try:
        target = validate_public_target(req.target)
        resolved_ip = resolve_public_target_ip(target)
    except (TargetValidationError, NetworkTargetError) as error:
        log_diagnostic_event(
            logging.WARNING,
            "diagnostic_target_rejected",
            request_id=request_id,
            target=req.target,
            reason=str(error),
        )
        raise HTTPException(status_code=400, detail=str(error)) from error

    log_diagnostic_event(
        logging.INFO,
        "diagnostic_started",
        request_id=request_id,
        target=target,
        resolved_ip=resolved_ip,
    )

    try:
        results = await execute_bounded_diagnostic(resolved_ip)
    except DiagnosticCapacityError as error:
        log_diagnostic_event(
            logging.WARNING,
            "diagnostic_capacity_rejected",
            request_id=request_id,
            target=target,
            resolved_ip=resolved_ip,
        )
        raise HTTPException(
            status_code=503,
            detail="Diagnostic capacity is currently full. Retry shortly.",
        ) from error
    except DiagnosticTimeoutError as error:
        log_diagnostic_event(
            logging.WARNING,
            "diagnostic_timed_out",
            request_id=request_id,
            target=target,
            resolved_ip=resolved_ip,
            timeout_seconds=settings.diagnostic_timeout_seconds,
        )
        raise HTTPException(
            status_code=504,
            detail="Diagnostic execution timed out before completion.",
        ) from error
    except Exception as error:
        log_diagnostic_event(
            logging.ERROR,
            "diagnostic_execution_failed",
            request_id=request_id,
            target=target,
            resolved_ip=resolved_ip,
            error_type=type(error).__name__,
        )
        raise HTTPException(
            status_code=502,
            detail="Diagnostic execution failed.",
        ) from error

    diagnostic_run = DiagnosticRun(
        target=target,
        ping_result=results["ping"],
        traceroute_result=results["traceroute"],
        port_results_json=json.dumps(results["ports"]),
    )

    try:
        db.add(diagnostic_run)
        db.commit()
        db.refresh(diagnostic_run)
    except SQLAlchemyError as error:
        db.rollback()
        log_diagnostic_event(
            logging.ERROR,
            "diagnostic_persistence_failed",
            request_id=request_id,
            target=target,
            resolved_ip=resolved_ip,
            error_type=type(error).__name__,
        )
        raise HTTPException(
            status_code=503,
            detail="Diagnostics completed but could not be saved.",
        ) from error

    log_diagnostic_event(
        logging.INFO,
        "diagnostic_completed",
        request_id=request_id,
        diagnostic_id=diagnostic_run.id,
        target=target,
        resolved_ip=resolved_ip,
    )

    return {
        "request_id": request_id,
        "diagnostic_id": diagnostic_run.id,
        "timestamp": datetime.now(UTC).isoformat(),
        "target": target,
        "resolved_ip": resolved_ip,
        "results": results,
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
