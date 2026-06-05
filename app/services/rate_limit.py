from time import time

AI_RATE_LIMIT_WINDOW_SECONDS = 60
AI_RATE_LIMIT_MAX_REQUESTS = 30

_ai_request_log: dict[str, list[float]] = {}


def reset_rate_limit_state() -> None:
    _ai_request_log.clear()


def is_ai_rate_limited(
    key: str,
    now: float | None = None,
    max_requests: int = AI_RATE_LIMIT_MAX_REQUESTS,
    window_seconds: int = AI_RATE_LIMIT_WINDOW_SECONDS,
) -> bool:
    current_time = time() if now is None else now
    window_start = current_time - window_seconds

    request_times = [
        request_time
        for request_time in _ai_request_log.get(key, [])
        if request_time >= window_start
    ]

    if len(request_times) >= max_requests:
        _ai_request_log[key] = request_times
        return True

    request_times.append(current_time)
    _ai_request_log[key] = request_times

    return False