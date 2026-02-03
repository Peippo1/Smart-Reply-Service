import time
from collections import defaultdict
from typing import Callable

from fastapi import HTTPException, Request, status

from app.core.config import get_settings


class SimpleRateLimiter:
    """
    In-memory sliding window limiter for quick MVP testing.
    Not suitable for multi-instance deployments.
    """

    def __init__(self, max_per_minute: int):
        self.max = max_per_minute
        self.hits: defaultdict[str, list[float]] = defaultdict(list)

    def check(self, key: str) -> None:
        now = time.time()
        window_start = now - 60
        self.hits[key] = [ts for ts in self.hits[key] if ts >= window_start]
        if len(self.hits[key]) >= self.max:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded.",
            )
        self.hits[key].append(now)


def rate_limit_dependency() -> Callable[[Request], None]:
    limiter = SimpleRateLimiter(get_settings().rate_limit_per_minute)

    async def _limit(request: Request) -> None:
        client_id = request.client.host if request.client else "unknown"
        limiter.check(client_id)

    return _limit

