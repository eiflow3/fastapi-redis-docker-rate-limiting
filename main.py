import os
import time
import uuid
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import redis.asyncio as aioredis
from middlewares.rate_limit import RateLimitMiddleware

RATE_LIMIT = int(os.getenv("RATE_LIMIT", "1000"))
WINDOW = int(os.getenv("WINDOW", "3600"))
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

app = FastAPI()

app.add_middleware(RateLimitMiddleware)


@app.on_event("startup")
async def startup():
    app.state.redis = aioredis.Redis(
        host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True
    )
    # ensure connection works
    try:
        await app.state.redis.ping()
        print("Connected to Redis")
    except Exception as e:
        print("Redis connection error:", e)
        raise


@app.on_event("shutdown")
async def shutdown():
    try:
        await app.state.redis.close()
        await app.state.redis.connection_pool.disconnect()
    except Exception:
        pass


# @app.middleware("http")
# async def rate_limit_middleware(request: Request, call_next):
#     # identify client — prefer X-API-Key, fallback to Authorization header, then client IP
#     client_id = request.headers.get("X-API-Key") or request.headers.get("Authorization") or request.client.host
#     if not client_id:
#         client_id = request.client.host

#     # sanitize (simple)
#     client_id = str(client_id).replace(" ", "_")

#     now = int(time.time())
#     window_start = now - (now % WINDOW)
#     key = f"ratelimit:{client_id}:{window_start}"

#     try:
#         count = await app.state.redis.incr(key)
#         if count == 1:
#             await app.state.redis.expire(key, WINDOW)
#     except Exception:
#         # Redis down -> fail-open: allow requests but don't provide accurate headers
#         response = await call_next(request)
#         response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)
#         response.headers["X-RateLimit-Remaining"] = str(RATE_LIMIT)
#         response.headers["X-RateLimit-Reset"] = str(window_start + WINDOW)
#         return response

#     remaining = max(RATE_LIMIT - count, 0)
#     reset_at = window_start + WINDOW

#     if count > RATE_LIMIT:
#         headers = {
#             "X-RateLimit-Limit": str(RATE_LIMIT),
#             "X-RateLimit-Remaining": "0",
#             "X-RateLimit-Reset": str(reset_at),
#         }
#         return JSONResponse(status_code=429, content={"detail": "Too Many Requests"}, headers=headers)

#     response = await call_next(request)
#     response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)
#     response.headers["X-RateLimit-Remaining"] = str(remaining)
#     response.headers["X-RateLimit-Reset"] = str(reset_at)
#     response.headers.setdefault("X-Request-ID", str(uuid.uuid4()))
#     return response

@app.delete("/cleanup")
async def cleanup_redis():
    try:
        await app.state.redis.flushdb()  # Deletes all keys in the current database
        return {"message": "Redis database flushed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to flush Redis: {str(e)}")


@app.get("/")
async def read_root():
    return {"message": "Hello world"}


@app.get("/health")
async def health(store_id: str):
    try:
        return {"status": "ok", "store_id": store_id}
    except HTTPException:
        raise