from threading import Lock
from time import time

AI_RATE_LIMIT_WINDOW_SECONDS = 60
AI_RATE_LIMIT_MAX_REQUESTS = 30
AI_RATE_LIMIT_MAX_CLIENTS = 5000

_ai_request_log: dict[str, list[float]] = {}
_rate_limit_lock = Lock()


def reset_rate_limit_state() -> None:
    with _rate_limit_lock:
        _ai_request_log.clear()


def rate_limit_state_size() -> int:
    with _rate_limit_lock:
        return len(_ai_request_log)


def _prune_stale_clients(window_start: float) -> None:
    stale_keys = [
        key
        for key, request_times in _ai_request_log.items()
        if not request_times or request_times[-1] < window_start
    ]
    for key in stale_keys:
        _ai_request_log.pop(key, None)


def _evict_oldest_client() -> None:
    if not _ai_request_log:
        return

    oldest_key = min(
        _ai_request_log,
        key=lambda key: _ai_request_log[key][-1] if _ai_request_log[key] else float("-inf"),
    )
    _ai_request_log.pop(oldest_key, None)


def is_ai_rate_limited(
    key: str,
    now: float | None = None,
    max_requests: int = AI_RATE_LIMIT_MAX_REQUESTS,
    window_seconds: int = AI_RATE_LIMIT_WINDOW_SECONDS,
    max_clients: int = AI_RATE_LIMIT_MAX_CLIENTS,
) -> bool:
    current_time = time() if now is None else now
    window_start = current_time - window_seconds

    with _rate_limit_lock:
        _prune_stale_clients(window_start)

        request_times = [
            request_time
            for request_time in _ai_request_log.get(key, [])
            if request_time >= window_start
        ]

        if len(request_times) >= max_requests:
            _ai_request_log[key] = request_times
            return True

        if key not in _ai_request_log and len(_ai_request_log) >= max_clients:
            _evict_oldest_client()

        request_times.append(current_time)
        _ai_request_log[key] = request_times
        return False
