# Backend Docker Setup Guide

This guide explains how to run the NotebookLM Backend API using Docker.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

## Quick Start

### 1. Create Environment File

Create a `.env` file in the `backend` directory with the following variables:

```env
# Database
# IMPORTANT: When running in Docker, use 'host.docker.internal' instead of 'localhost'
# to connect to PostgreSQL running on your host machine
# If using docker-compose, use 'postgres' as the hostname
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
DATABASE_NAME=notebooklm
DATABASE_PORT=5432
# For Docker (standalone): Use host.docker.internal
DATABASE_URL=postgresql+asyncpg://postgres:postgres@host.docker.internal:5432/notebooklm
# For docker-compose: Use postgres service name
# DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/notebooklm

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Server
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# Frontend URL
FRONTEND_URL=http://localhost:3000

# API Keys
OPENROUTER_API_KEY=your-openrouter-api-key
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=your-qdrant-api-key

# Ports
QDRANT_PORT=6333
QDRANT_GRPC_PORT=6334
```

### 2. Build and Run

```bash
cd backend

# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### 3. Run Database Migrations

```bash
# Run migrations in the backend container
docker-compose exec backend uv run alembic upgrade head
```

### 4. Access Services

- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Qdrant**: http://localhost:6333
- **PostgreSQL**: localhost:5432

## Development Mode

For development with hot reload:

```bash
cd backend

# Start in development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or build and start
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

## Running with Dockerfile Only (Without Docker Compose)

You can run the backend using just the Dockerfile without docker-compose:

### 1. Build the Image

```bash
cd backend
docker build -t notebooklm-backend .
```

### 2. Run the Container

#### Option A: Using .env file

**IMPORTANT:** Make sure your `.env` file uses `host.docker.internal` (Windows/Mac) or `172.17.0.1` (Linux) instead of `localhost` for `DATABASE_URL` when connecting to PostgreSQL on your host machine.

```bash
docker run -d \
  --name notebooklm-backend \
  -p 8000:8000 \
  --env-file .env \
  --add-host=host.docker.internal:host-gateway \
  notebooklm-backend
```

**Note:** The `--add-host=host.docker.internal:host-gateway` flag enables connection to services on your host machine from within the Docker container.

#### Option B: Using environment variables directly

```bash
docker run -d \
  --name notebooklm-backend \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname \
  -e JWT_SECRET_KEY=your-secret-key \
  -e BACKEND_CORS_ORIGINS=http://localhost:3000 \
  -e OPENROUTER_API_KEY=your-api-key \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/uploads:/app/uploads \
  notebooklm-backend
```

#### Option C: With volume mounts for persistent data

```bash
docker run -d \
  --name notebooklm-backend \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/qdrant_db:/app/qdrant_db \
  notebooklm-backend
```

### 3. View Logs

```bash
docker logs -f notebooklm-backend
```

### 4. Stop and Remove

```bash
docker stop notebooklm-backend
docker rm notebooklm-backend
```

## Individual Services

### Build Backend Only

```bash
cd backend
docker build -t notebooklm-backend .
docker run -p 8000:8000 --env-file .env notebooklm-backend
```

### Run Backend with External Database

If you have an external PostgreSQL database, you can run just the backend:

```bash
cd backend
docker build -t notebooklm-backend .
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname \
  -e JWT_SECRET_KEY=your-secret \
  -e BACKEND_CORS_ORIGINS=http://localhost:3000 \
  notebooklm-backend
```

## Production Deployment

### 1. Update Environment Variables

Ensure all production values are set in `.env`:
- Strong `JWT_SECRET_KEY`
- Production database credentials
- Production CORS origins
- Production frontend URL

### 2. Build Production Images

```bash
cd backend
docker-compose build --no-cache
```

### 3. Run in Production Mode

```bash
cd backend
docker-compose up -d
```

## Troubleshooting

### Backend Issues

```bash
# Check backend logs
docker-compose logs backend

# Access backend container
docker-compose exec backend bash

# Run migrations manually
docker-compose exec backend uv run alembic upgrade head

# Check Python environment
docker-compose exec backend uv run python --version
```

### Database Issues

```bash
# Check database logs
docker-compose logs postgres

# Access database
docker-compose exec postgres psql -U postgres -d notebooklm

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d postgres
```

### Qdrant Issues

```bash
# Check Qdrant logs
docker-compose logs qdrant

# Access Qdrant container
docker-compose exec qdrant sh
```

### Volume Issues

```bash
# Check volume mounts
docker-compose ps
docker volume ls

# Clean up volumes
docker-compose down -v
```

## Docker Compose Services

- **postgres**: PostgreSQL database
- **backend**: FastAPI backend API
- **qdrant**: Qdrant vector database (optional)

## Volumes

The following directories are mounted as volumes:
- `./logs` → Backend logs
- `./outputs` → Generated outputs (podcasts, etc.)
- `./uploads` → User uploaded files
- `./qdrant_db` → Local Qdrant database files

## Health Checks

All services include health checks:
- Backend: `GET /health`
- PostgreSQL: `pg_isready`

## Security Notes

1. **Never commit `.env` files** - They contain sensitive credentials
2. **Use strong JWT secrets** in production
3. **Configure CORS properly** for production domains
4. **Use HTTPS** in production (via reverse proxy)
5. **Regularly update** Docker images for security patches

