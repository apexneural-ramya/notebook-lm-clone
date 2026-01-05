# Frontend Docker Setup Guide

This guide explains how to run the NotebookLM Frontend application using Docker.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

## Quick Start

### 1. Create Environment File

Create a `.env` file in the `frontend` directory with the following variables:

```env
# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Ports
FRONTEND_PORT=3000
```

### 2. Build and Run

```bash
cd frontend

# Build and start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop service
docker-compose down
```

### 3. Access Frontend

- **Frontend**: http://localhost:3000

## Development Mode

For development with hot reload:

```bash
cd frontend

# Start in development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or build and start
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

## Running with Dockerfile Only (Without Docker Compose)

You can run the frontend using just the Dockerfile without docker-compose:

### 1. Build the Image

```bash
cd frontend
docker build -t notebooklm-frontend .
```

### 2. Run the Container

#### Option A: Using .env file

```bash
docker run -d \
  --name notebooklm-frontend \
  -p 3000:3000 \
  --env-file .env \
  notebooklm-frontend
```

#### Option B: Using environment variables directly

```bash
docker run -d \
  --name notebooklm-frontend \
  -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://localhost:8000 \
  notebooklm-frontend
```

### 3. View Logs

```bash
docker logs -f notebooklm-frontend
```

### 4. Stop and Remove

```bash
docker stop notebooklm-frontend
docker rm notebooklm-frontend
```

## Individual Service

### Build Frontend Only

```bash
cd frontend
docker build -t notebooklm-frontend .
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://localhost:8000 notebooklm-frontend
```

## Production Deployment

### 1. Update Environment Variables

Ensure all production values are set in `.env`:
- Production backend API URL
- Production port (if different from 3000)

### 2. Build Production Image

```bash
cd frontend
docker-compose build --no-cache
```

### 3. Run in Production Mode

```bash
cd frontend
docker-compose up -d
```

### 4. Set Up Reverse Proxy (Optional)

For production, use nginx or Traefik as a reverse proxy:

```nginx
# nginx.conf example
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Troubleshooting

### Frontend Issues

```bash
# Check frontend logs
docker-compose logs frontend

# Access frontend container
docker-compose exec frontend sh

# Rebuild frontend
docker-compose build frontend --no-cache
docker-compose up -d frontend

# Check Node version
docker-compose exec frontend node --version
```

### Build Issues

```bash
# Clean build
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check build logs
docker-compose build --progress=plain
```

### Port Conflicts

If port 3000 is already in use:

```bash
# Use a different port
FRONTEND_PORT=3001 docker-compose up -d
```

## Docker Compose Services

- **frontend**: Next.js frontend application

## Health Checks

The service includes health checks:
- Frontend: HTTP check on port 3000

## Security Notes

1. **Never commit `.env` files** - They may contain sensitive configuration
2. **Use HTTPS** in production (via reverse proxy)
3. **Regularly update** Docker images for security patches
4. **Configure CORS** properly on the backend for production domains

## Connecting to Backend

The frontend needs to connect to the backend API. Make sure:

1. The backend is running and accessible
2. `NEXT_PUBLIC_API_URL` is set correctly in `.env`
3. CORS is properly configured on the backend
4. Both services are on the same network or accessible to each other

If running backend and frontend separately:
- Backend should be accessible at the URL specified in `NEXT_PUBLIC_API_URL`
- For Docker networks, use service names (e.g., `http://backend:8000`)
- For local development, use `http://localhost:8000`

