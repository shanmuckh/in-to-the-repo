"""
Rate limiting configuration for the application.
Uses slowapi for implementing per-endpoint rate limits.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI

# Initialize the rate limiter
limiter = Limiter(key_func=get_remote_address)


def init_limiter(app: FastAPI):
    """
    Initialize the rate limiter with the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    app.state.limiter = limiter
    # Add exception handler for rate limit exceeded
    from slowapi.errors import RateLimitExceeded
    from fastapi.responses import JSONResponse
    
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_exceeded_handler(request, exc):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please try again later."}
        )
