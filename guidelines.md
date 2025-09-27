# FastAPI + Redis with Docker — Step-by-step

A practical, copy‑pasteable guide to run a FastAPI app that uses Redis (for rate limiting, caching, etc.) with Docker and Docker Compose. Includes files, Docker commands, test commands, and notes for production.

---

## Overview

What you’ll get:
- A small FastAPI app (`main.py`) that connects to Redis using `redis.asyncio`.
- Rate‑limiting middleware that stores counters in Redis and returns `X-RateLimit-*` headers.
- `Dockerfile` for the API and `docker-compose.yml` to run API + Redis together.
- `.env.example`, `requirements.txt`, and testing instructions.

Prerequisites:
- Docker & Docker Compose installed locally.
- Basic familiarity with the terminal.

---

## Project structure

```
fastapi-redis-docker/
├─ Dockerfile
├─ docker-compose.yml
├─ .env.example
├─ requirements.txt
└─ main.py
```

---

## 1) `requirements.txt`

```
fastapi
uvicorn[standard]
redis
```

> `redis` (redis-py) is used here with its async interface (`redis.asyncio`).

---

## 2) `Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app

# install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

# Run uvicorn (use Gunicorn+UvicornWorker in production if you want multiple workers)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 3) `docker-compose.yml`

```yaml
version: "3.8"
services:
  api:
    build: .
    container_name: fastapi-api
    ports:
      - "8000:8000"
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - RATE_LIMIT=${RATE_LIMIT:-1000}
      - WINDOW=${WINDOW:-3600}
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7
    container_name: fastapi-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: ["redis-server", "--appendonly", "yes"]

volumes:
  redis-data:
```

---

## 4) `.env.example`

```
REDIS_HOST=redis
REDIS_PORT=6379
RATE_LIMIT=1000
WINDOW=3600
```

Copy to `.env` and edit values for development if needed.

---

## 5) `main.py` (copy-paste)

```python
import os
import time
import uuid
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import redis.asyncio as aioredis

RATE_LIMIT = int(os.getenv("RATE_LIMIT", "1000"))
WINDOW = int(os.getenv("WINDOW", "3600"))
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

app = FastAPI()

@app.on_event("startup")
async def startup():
    app.state.redis = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
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

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # identify client — prefer X-API-Key, fallback to Authorization header, then client IP
    client_id = request.headers.get("X-API-Key") or request.headers.get("Authorization") or request.client.host
    if not client_id:
        client_id = request.client.host

    # sanitize (simple)
    client_id = str(client_id).replace(" ", "_")

    now = int(time.time())
    window_start = now - (now % WINDOW)
    key = f"ratelimit:{client_id}:{window_start}"

    try:
        count = await app.state.redis.incr(key)
        if count == 1:
            await app.state.redis.expire(key, WINDOW)
    except Exception:
        # Redis down -> fail-open: allow requests but don't provide accurate headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)
        response.headers["X-RateLimit-Remaining"] = str(RATE_LIMIT)
        response.headers["X-RateLimit-Reset"] = str(window_start + WINDOW)
        return response

    remaining = max(RATE_LIMIT - count, 0)
    reset_at = window_start + WINDOW

    if count > RATE_LIMIT:
        headers = {
            "X-RateLimit-Limit": str(RATE_LIMIT),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(reset_at),
        }
        return JSONResponse(status_code=429, content={"detail": "Too Many Requests"}, headers=headers)

    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset_at)
    response.headers.setdefault("X-Request-ID", str(uuid.uuid4()))
    return response


@app.get("/")
async def read_root():
    return {"message": "Hello world"}


@app.get("/health")
async def health():
    return {"status": "ok"}
```

---

## 6) Build & run (development)

```bash
# from project root
# build + start
docker compose up --build

# or in background
docker-compose up --build -d

# view logs
docker-compose logs -f api
```

Open `http://localhost:8000/` and `http://localhost:8000/health`.

---

## 7) Test rate limiting with curl

Lower the limit for quick testing (edit `.env` or override env when running compose):
```
RATE_LIMIT=5
WINDOW=60
```

Then run a loop to exceed the limit:

```bash
for i in {1..7}; do \
  echo "REQUEST $i"; \
  curl -i -H "X-API-Key: test-user" http://localhost:8000/; \
  echo; \
done
```

You should see `X-RateLimit-Remaining` decrease and a `429` response after the 5th request.

---

## 8) Inspect Redis keys (optional)

```bash
# exec into redis container
docker exec -it fastapi-redis redis-cli
# then in redis-cli
KEYS ratelimit:*
GET ratelimit:test-user:<window_start>
```

---

## 9) Scaling & production notes

- **Scaling:** run multiple API replicas (e.g., `docker-compose up --scale api=3`) — all replicas will share the same Redis backend so rate limits remain consistent.

- **Redis password:** for production, enable AUTH and use `redis://:PASSWORD@host:port` in the Redis client. Do not hardcode creds — use Docker secrets or cloud provider secrets.

- **Persistence & HA:** use Redis persistence (`appendonly yes`) and consider managed Redis (ElastiCache, Memorystore) or Redis Cluster for high availability.

- **Better algorithms:** this guide uses **fixed window**. For smoother behavior use **sliding window** or **token bucket** (allow bursts + refill). Libraries and more complex Lua scripts in Redis help implement those.

- **Edge rate limiting:** consider offloading rate limiting to an API gateway (NGINX, Traefik, Kong, Cloudflare) for better performance and separation of concerns.

- **Use Gunicorn+UvicornWorker** in the Dockerfile when you need multiple workers:

```dockerfile
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "main:app", "--workers", "4"]
```

- **Behind proxies:** if your service is behind a proxy/load balancer, extract the real client IP from `X-Forwarded-For` (trust proxy config).

---

## 10) Troubleshooting

- `Redis connection error` on startup: ensure the `redis` service is healthy and reachable by container name `redis`.
- `Too Many Requests` but you think it shouldn't: confirm `X-API-Key` or Authorization header is what you expect (client id key).
- `Inconsistent limits` when scaling: check that all replicas point to the same Redis host.

---

## Want a Kubernetes YAML or a production hardened Docker Compose?
If you’d like, I can also:
- Provide a **production Dockerfile** using `gunicorn + Uvicorn` and multi-stage build.
- Generate **Kubernetes manifests** (Deployment, Service, HPA, ConfigMap, Secret) with readiness/liveness probes.
- Replace the fixed-window rate limiter with a **token-bucket** implementation (Lua script) for smoother behavior.

Tell me which one and I’ll add it next.

