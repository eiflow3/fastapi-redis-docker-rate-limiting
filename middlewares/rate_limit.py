from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from fastapi import Request, HTTPException
from fastapi import status as fastapi_status
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        strict: bool = False,
        max_requests: int = 4,
        window_minutes: int = 30,
        bypass_paths: Optional[List[str]] = None,
    ):
        super().__init__(app)
        self.strict = strict
        self.max_requests = max_requests
        self.window_minutes = window_minutes
        self.bypass_paths = bypass_paths or ["/health"]
        self.logger = logging.getLogger(__name__)
        # Set up logging if not already configured
        if not logging.getLogger().hasHandlers():
            logging.basicConfig(level=logging.INFO)

    def _parse_feature_endpoint(self, path: str) -> str:
        """
        Parse the URL path to extract the feature and endpoint, ignoring version, service name, and public/internal prefixes.

        Args:
            path (str): The full URL path.

        Returns:
            str: The parsed feature/endpoint path.
        """
        # Strip leading slash and split into parts
        parts = path.strip("/").split("/")
        # Remove version prefix if present (e.g., v1, v2)
        if parts and parts[0].startswith("v") and parts[0][1:].isdigit():
            parts = parts[1:]
        # Remove service name (next part after version)
        if parts:
            parts = parts[1:]
        # Remove public/internal if present
        if parts and parts[0] in ["public", "internal"]:
            parts = parts[1:]
        # Join remaining parts as feature/endpoint
        return "/".join(parts) if parts else ""

    async def dispatch(self, request: Request, call_next):
        # Bypass rate limiting for specified paths if not in strict mode
        if not self.strict and request.url.path in self.bypass_paths:
            self.logger.debug(f"Bypassing rate limit for path: {request.url.path}")
            return await call_next(request)

        # Extract store_id from query params
        store_id = request.query_params.get("store_id")
        if not store_id:
            # If no store_id, skip rate limiting or handle as needed
            self.logger.warning(
                "No store_id provided in query params, skipping rate limiting"
            )
            return await call_next(request)

        # Extract path (endpoint name) - feature + endpoint only
        path = self._parse_feature_endpoint(request.url.path)
        self.logger.debug(f"Parsed feature/endpoint path: {path}")

        # Create Redis key
        key = f"{store_id}_{path}"
        self.logger.debug(f"Redis key: {key}")

        try:
            # Get existing data from Redis
            data_str = await request.app.state.redis.get(key)
            if data_str:
                data = json.loads(data_str)
                self.logger.debug(f"Existing rate limit data: {data}")
                if data["api-remaining-request"] <= 0:
                    # Return 429 response directly instead of raising exception
                    self.logger.warning(f"Rate limit exceeded for key: {key}")
                    return JSONResponse(
                        status_code=fastapi_status.HTTP_429_TOO_MANY_REQUESTS,
                        content={"detail": "Rate limit exceeded"},
                        headers={
                            "X-Rate-Limit-Remaining": "0",
                            "X-Rate-Limit-Reset": str(int(data["api-requests-reset"])),
                        },
                    )
                data["api-remaining-request"] -= 1
            else:
                # Create new entry
                reset_time = datetime.now() + timedelta(minutes=self.window_minutes)
                data = {
                    "api-remaining-request": self.max_requests
                    - 1,  # Already used one request
                    "api-requests-reset": reset_time.timestamp(),
                }
                self.logger.info(f"Created new rate limit entry for key: {key}")

            # Save back to Redis with TTL (window_minutes * 60 seconds)
            ttl_seconds = self.window_minutes * 60
            await request.app.state.redis.setex(key, ttl_seconds, json.dumps(data))
            self.logger.debug(f"Saved rate limit data to Redis with TTL: {ttl_seconds}")

        except Exception as e:
            # Log the error and allow the request to proceed to avoid blocking legitimate traffic
            self.logger.error(f"Error accessing Redis for key {key}: {e}")
            # Optionally, you could return a 500 error or proceed without rate limiting
            return await call_next(request)

        # Proceed with the request
        response = await call_next(request)

        # Set rate limit headers on response
        response.headers["X-Rate-Limit-Remaining"] = str(data["api-remaining-request"])
        response.headers["X-Rate-Limit-Reset"] = str(int(data["api-requests-reset"]))

        return response
