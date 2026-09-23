"""Konfigurasi rate limiting dengan slowapi."""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI


def get_client_ip(request) -> str:
    """Ambil IP client dari header proxy atau langsung."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=get_client_ip, default_limits=[])


def setup_rate_limit(app: FastAPI) -> None:
    """Pasang limiter + exception handler ke FastAPI app."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
