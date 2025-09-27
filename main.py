import os
import time
import uuid
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import redis.asyncio as aioredis
from middlewares.rate_limit import RateLimitMiddleware
import logging as logger

RATE_LIMIT = int(os.getenv("RATE_LIMIT", "5"))
WINDOW = int(os.getenv("WINDOW", "1"))
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Set up logging
logger.basicConfig(level=logger.INFO)

app = FastAPI()

app.add_middleware(
    RateLimitMiddleware,
    strict=False,
    max_requests=RATE_LIMIT,
    window_minutes=WINDOW,
)


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

@app.delete("/cleanup")
async def cleanup_redis():
    try:
        await app.state.redis.flushdb()  # Deletes all keys in the current database
        return {"message": "Redis database flushed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to flush Redis: {str(e)}")


# Store id acts as requestor identifier for rate limiting to create unique keys in redis
@app.get("/v1/service/feature/one")
async def feature_1(store_id: str):
    try:
        logger.info("Calling feature-1 endpoint")
        return {"feature": "feature-1", "store_id": store_id}
    except HTTPException:
        raise


@app.get("/v2/service/fature/two")
async def feature_2(store_id: str):
    try:
        logger.info("Calling feature-2 endpoint")
        return {"feature": "feature-2", "store_id": store_id}
    except HTTPException:
        raise


@app.get("/health")
async def health(store_id: str):
    try:
        return {"status": "ok", "store_id": store_id}
    except HTTPException:
        raise
