# FastAPI Redis Docker Rate Limiting

A robust FastAPI application implementing configurable rate limiting using Redis, containerized with Docker for easy deployment and scalability.

## 🚀 Features

- **FastAPI Framework**: High-performance, modern Python web framework
- **Redis-based Rate Limiting**: Distributed rate limiting with Redis backend
- **Configurable Rate Limits**: Environment-based configuration for requests and time windows
- **Docker Containerization**: Easy deployment with Docker and Docker Compose
- **Middleware Implementation**: Custom rate limiting middleware for per-store, per-endpoint limits
- **Agnostic Path Extraction**: Intelligently extracts feature/endpoint paths, ignoring service versions and prefixes
- **Health Check Endpoint**: Built-in health monitoring with rate limit bypass option
- **Cleanup Endpoint**: Administrative endpoint for Redis data management
- **Comprehensive Logging**: Built-in logging for monitoring and debugging
- **Error Handling**: Fail-open strategy for Redis unavailability

## 📋 Rate Limiting Specifications

The application implements configurable rate limiting based on:

- **Store ID**: Identified via `store_id` query parameter
- **Endpoint Path**: Rate limits are applied per feature/endpoint (ignoring service version, name, and access prefixes)
- **Configurable Limits**: Set via environment variables `RATE_LIMIT` and `WINDOW`
- **Redis Key Format**: `{store_id}_{feature/endpoint}`

### Default Configuration

- **Max Requests**: 5 per window (configurable via `RATE_LIMIT`)
- **Time Window**: 1 minute (configurable via `WINDOW` in minutes)
- **Bypass Paths**: `/health` (when strict mode is disabled)

When rate limit is exceeded, returns HTTP 429 with appropriate headers:

- `X-Rate-Limit-Remaining`: Remaining requests in current window
- `X-Rate-Limit-Reset`: Timestamp when the limit resets

## 🛠️ Installation & Setup

### Prerequisites

- Docker and Docker Compose
- Git

### Clone the Repository

```bash
git clone https://github.com/eiflow3/fastapi-redis-docker-rate-limiting.git
cd fastapi-redis-docker-rate-limiting
```

### Environment Variables

Configure the following environment variables (optional, defaults provided):

- `RATE_LIMIT`: Maximum requests per window (default: 5)
- `WINDOW`: Time window in minutes (default: 1)
- `REDIS_HOST`: Redis host (default: redis)
- `REDIS_PORT`: Redis port (default: 6379)
- `REDIS_DB`: Redis database number (default: 0)

### Run with Docker Compose

```bash
# Build and start the services
docker-compose up --build

# Run in background
docker-compose up -d --build
```

The API will be available at `http://localhost:8000`

## 📖 API Endpoints

### GET /v1/service/feature/one

Feature endpoint for service v1.

**Parameters:**

- `store_id` (query, required): Store identifier for rate limiting

**Response:**

```json
{
  "feature": "feature-1",
  "store_id": "123456"
}
```

### GET /v2/service/feature/two

Feature endpoint for service v2.

**Parameters:**

- `store_id` (query, required): Store identifier for rate limiting

**Response:**

```json
{
  "feature": "feature-2",
  "store_id": "123456"
}
```

### GET /health

Health check endpoint. Bypasses rate limiting by default.

**Parameters:**

- `store_id` (query, required): Store identifier

**Response:**

```json
{
  "status": "ok",
  "store_id": "123456"
}
```

### DELETE /cleanup

Administrative endpoint to flush Redis database.

**Response:**

```json
{
  "message": "Redis database flushed successfully"
}
```

## 🔧 Development

### Local Development (without Docker)

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start Redis server (locally or via Docker):

```bash
docker run -d -p 6379:6379 redis:7
```

3. Run the application:

```bash
uvicorn main:app --reload
```

### Testing Rate Limiting

Test the rate limiting by making multiple requests to an endpoint:

```bash
# This should work (first few requests)
curl "http://localhost:8000/v1/service/feature/one?store_id=123456"

# After exceeding the limit, you'll get 429:
# HTTP 429 Too Many Requests
# Headers: X-Rate-Limit-Remaining: 0, X-Rate-Limit-Reset: <timestamp>
```

## 🏗️ Architecture

- **main.py**: FastAPI application with Redis connection management and route definitions
- **middlewares/rate_limit.py**: Custom middleware implementing rate limiting logic with configurable parameters
- **Dockerfile**: Container configuration for the API service
- **docker-compose.yml**: Multi-service setup with API and Redis
- **enhancement.md**: Detailed enhancement plan and assessment
- **rate-limit-specs.md**: Comprehensive rate limiting specifications
- **middleware_docs.md**: Documentation explaining middleware implementation

## 📁 Project Structure

```
.
├── main.py                    # FastAPI application
├── middlewares/
│   └── rate_limit.py          # Rate limiting middleware
├── requirements.txt           # Python dependencies
├── Dockerfile                # Docker image configuration
├── docker-compose.yml        # Docker services orchestration
├── rate-limit-specs.md       # Rate limiting specifications
├── middleware_docs.md        # Middleware documentation
├── guidelines.md             # Project guidelines
├── .github/
│   └── instructions/
│       └── code-creation.md.instructions.md  # Code creation guidelines
└── README.md                # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

If you have any questions or issues, please open an issue on GitHub.
