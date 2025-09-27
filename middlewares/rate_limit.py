from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from fastapi import Request, HTTPException
import json
from datetime import datetime, timedelta


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # Extract store_id from query params
        store_id = request.query_params.get("store_id")
        if not store_id:
            # If no store_id, skip rate limiting or handle as needed
            return await call_next(request)

        # Extract path (endpoint name)
        path = request.url.path.lstrip("/")

        # Create Redis key
        key = f"{store_id}_{path}"

        # Get existing data
        data_str = await request.app.state.redis.get(key)
        if data_str:
            data = json.loads(data_str)
            if data["api-remaining-request"] <= 0:
                # Return 429 response directly instead of raising exception
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"},
                    headers={
                        "X-Rate-Limit-Remaining": "0",
                        "X-Rate-Limit-Reset": str(int(data["api-requests-reset"])),
                    },
                )
            data["api-remaining-request"] -= 1
        else:
            # Create new entry
            reset_time = datetime.now() + timedelta(minutes=30)
            data = {
                "api-remaining-request": 4,
                "api-requests-reset": reset_time.timestamp(),
            }

        # Save back to Redis with TTL 30 mins (1800 seconds)
        await request.app.state.redis.setex(key, 1800, json.dumps(data))

        # Proceed with the request
        response = await call_next(request)

        # Set rate limit headers on response
        response.headers["X-Rate-Limit-Remaining"] = str(data["api-remaining-request"])
        response.headers["X-Rate-Limit-Reset"] = str(int(data["api-requests-reset"]))

        return response
