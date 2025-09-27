# Rate Limiting Specifications

## Overview

This document outlines the rate limiting logic implemented in the FastAPI application using Redis as the backend store.

## Rate Limiting Flow

For a user request to an endpoint such as `/health?store_id=123456`:

1. **Extract Path**: Get the endpoint path, e.g., "health"
2. **Extract Store ID**: Get the `store_id` query parameter, e.g., "123456"
3. **Redis Key**: Construct the key as `{store_id}_{path}`, e.g., `123456_health`

### If Key Does Not Exist in Redis

- Create a new entry with a TTL of 30 minutes
- Store an object with the following structure:
  ```json
  {
    "api-remaining-request": 4,
    "api-requests-reset": <UTC timestamp of creation + 30 minutes>
  }
  ```

### If Key Exists in Redis

- Check if `api-remaining-request` <= 0:
  - If true, return HTTP 429 (Too Many Requests)
- Otherwise:
  - Decrement `api-remaining-request` by 1

## Notes

- The rate limit allows up to 4 requests per 30-minute window per store ID and endpoint combination.
- The Redis key expires after 30 minutes, resetting the limit.
- Response headers include rate limit information for client awareness.
