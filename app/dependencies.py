from collections import defaultdict
from time import time

from fastapi import Depends, HTTPException, status

from app.config import settings
from app.models import User
from app.services.auth import get_current_user


me_request_history = defaultdict(list)


def rate_limit_me(current_user: User = Depends(get_current_user)) -> User:
    now = time()
    window_start = now - settings.rate_limit_window_seconds
    history = [timestamp for timestamp in me_request_history[current_user.id] if timestamp > window_start]

    if len(history) >= settings.rate_limit_me_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests to /me. Please try again later.",
        )

    history.append(now)
    me_request_history[current_user.id] = history
    return current_user
