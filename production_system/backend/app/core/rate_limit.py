import time
from collections import defaultdict, deque
from typing import Deque

from fastapi import HTTPException, Request

from app.core.config import get_settings


_BUCKETS: dict[str, Deque[float]] = defaultdict(deque)


async def enforce_rate_limit(request: Request) -> None:
    settings = get_settings()
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    window_start = now - 60.0
    bucket = _BUCKETS[ip]

    while bucket and bucket[0] < window_start:
        bucket.popleft()

    if len(bucket) >= settings.max_requests_per_minute:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    bucket.append(now)
