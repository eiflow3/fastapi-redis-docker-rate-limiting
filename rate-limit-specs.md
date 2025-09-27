# Rate Limiting Specifications

## Overview

This document outlines the rate limiting logic implemented in the FastAPI application using Redis as the backend store. The rate limiting is handled by the `RateLimitMiddleware` class, which provides configurable rate limiting based on store ID and endpoint paths.

## Configuration Parameters

The middleware accepts the following configuration parameters:

- `strict` (bool, default: False): Whether to apply rate limiting to bypass paths like `/health`
- `max_requests` (int, default: 4): Maximum number of requests allowed per window
- `window_minutes` (int, default: 30): Time window in minutes for rate limiting
- `bypass_paths` (List[str], default: ["/health"]): Paths that bypass rate limiting when strict=False

## Path Extraction Logic

The system extracts the "feature/endpoint" portion of the URL path for rate limiting keys, ignoring:

- Service version prefixes (e.g., `/v1/`, `/v2/`)
- Service name (e.g., `/service/`)
- Access level prefixes (e.g., `/public/`, `/internal/`)

The path parsing is handled by the `_parse_feature_endpoint()` method in `RateLimitMiddleware`.

Examples:

- `/v1/service/logo/generate` → `logo/generate`
- `/v1/service/public/logo/generate` → `logo/generate`
- `/v1/service/feature/one` → `feature/one`
- `/health` → `health`

## Strict Mode

The rate limiting behavior can be controlled via the `strict` parameter:

- **strict=True**: Rate limiting applies to all endpoints, including those in `bypass_paths`
- **strict=False** (default): Endpoints in `bypass_paths` (default: `/health`) bypass rate limiting

## Rate Limiting Flow

For a user request to an endpoint such as `/v1/service/feature/one?store_id=123456`:

1. **Check Bypass**: If not in strict mode and path is in `bypass_paths`, skip rate limiting
2. **Extract Store ID**: Get the `store_id` query parameter. If missing, skip rate limiting and log a warning
3. **Extract Path**: Parse the URL path using `_parse_feature_endpoint()` to get the feature/endpoint
4. **Construct Redis Key**: Create key as `{store_id}_{path}`, e.g., `123456_feature/one`
5. **Check Redis**: Attempt to get existing rate limit data from Redis

### If Key Does Not Exist in Redis

- Create a new entry with TTL of `window_minutes * 60` seconds
- Store an object with the following structure:
  ```json
  {
    "api-remaining-request": max_requests - 1,  // Already decremented for current request
    "api-requests-reset": <UTC timestamp of creation + window_minutes>
  }
  ```

### If Key Exists in Redis

- Parse the JSON data from Redis
- Check if `api-remaining-request` <= 0:
  - If true, return HTTP 429 (Too Many Requests) with appropriate headers
- Otherwise:
  - Decrement `api-remaining-request` by 1
  - Update the data in Redis with the same TTL

### Error Handling

- If Redis operations fail, log the error and allow the request to proceed (fail-open strategy)
- This prevents blocking legitimate traffic due to Redis unavailability

## Response Headers

Successful requests include the following headers:

- `X-Rate-Limit-Remaining`: Number of requests remaining in the current window
- `X-Rate-Limit-Reset`: Unix timestamp when the rate limit resets

Rate-limited requests (429) include:

- `X-Rate-Limit-Remaining`: 0
- `X-Rate-Limit-Reset`: Unix timestamp when the limit resets

## Environment Variables

The application uses the following environment variables for configuration:

- `RATE_LIMIT`: Maximum requests per window (default: 5 in main.py, but configurable)
- `WINDOW`: Window duration in minutes (default: 1 in main.py, but configurable)
- `REDIS_HOST`: Redis host (default: "redis")
- `REDIS_PORT`: Redis port (default: 6379)
- `REDIS_DB`: Redis database number (default: 0)

## Logging

The middleware includes comprehensive logging:

- Debug logs for path parsing, key construction, and Redis operations
- Warning logs for missing store_id or rate limit exceeded
- Error logs for Redis failures
- Info logs for new rate limit entries

## Notes

- The rate limit window is sliding in the sense that keys expire after the full window duration
- Each unique combination of store_id and parsed endpoint path has its own rate limit
- The middleware uses Redis TTL for automatic cleanup of expired rate limit data
- The implementation prioritizes availability (fail-open on Redis errors) over strict enforcement
