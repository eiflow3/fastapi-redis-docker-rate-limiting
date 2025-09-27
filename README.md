git branch -M main# FastAPI Redis Docker Rate Limiting

A robust FastAPI application implementing rate limiting using Redis, containerized with Docker for easy deployment and scalability.

## 🚀 Features

- **FastAPI Framework**: High-performance, modern Python web framework
- **Redis-based Rate Limiting**: Distributed rate limiting with Redis backend
- **Docker Containerization**: Easy deployment with Docker and Docker Compose
- **Middleware Implementation**: Custom rate limiting middleware for per-store, per-endpoint limits
- **Health Check Endpoint**: Built-in health monitoring
- **Cleanup Endpoint**: Administrative endpoint for Redis data management

## 📋 Rate Limiting Specifications

The application implements rate limiting based on:

- **Store ID**: Identified via `store_id` query parameter
- **Endpoint Path**: Rate limits are applied per endpoint
- **Limit**: 4 requests per 30-minute window
- **Redis Key Format**: `{store_id}_{path}`

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

- `RATE_LIMIT`: Maximum requests per window (default: 1000)
- `WINDOW`: Time window in seconds (default: 3600)
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

### GET /

Basic hello world endpoint.

**Response:**

```json
{
  "message": "Hello world"
}
```

### GET /health

Health check endpoint requiring `store_id` parameter.

**Parameters:**

- `store_id` (query): Store identifier for rate limiting

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

Test the rate limiting by making multiple requests to `/health?store_id=123456`:

```bash
# This should work (first few requests)
curl "http://localhost:8000/health?store_id=123456"

# After 4 requests within 30 minutes, you'll get 429:
# HTTP 429 Too Many Requests
```

## 🏗️ Architecture

- **main.py**: FastAPI application with Redis connection management
- **middlewares/rate_limit.py**: Custom middleware implementing rate limiting logic
- **Dockerfile**: Container configuration for the API service
- **docker-compose.yml**: Multi-service setup with API and Redis

## 📁 Project Structure

```
.
├── main.py                 # FastAPI application
├── middlewares/
│   └── rate_limit.py       # Rate limiting middleware
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker image configuration
├── docker-compose.yml     # Docker services orchestration
├── rate-limit-specs.md    # Rate limiting specifications
├── docker_cheatsheet.md   # Docker commands reference
├── guidelines.md          # Project guidelines
└── README.md             # This file
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
