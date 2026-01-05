#!/bin/bash
# Script to run backend using Dockerfile only

set -e

echo "Building NotebookLM Backend Docker image..."
docker build -t notebooklm-backend .

echo "Stopping existing container (if any)..."
docker stop notebooklm-backend 2>/dev/null || true
docker rm notebooklm-backend 2>/dev/null || true

echo "Starting NotebookLM Backend container..."
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please create a .env file in the backend directory with required environment variables."
    echo "Example:"
    echo "  DATABASE_URL=postgresql+asyncpg://postgres:CHANGE_THIS_PASSWORD@host.docker.internal:5432/notebooklm"
    echo "  Note: Use 'host.docker.internal' instead of 'localhost' for DATABASE_URL when running in Docker"
    echo "  JWT_SECRET_KEY=CHANGE_THIS_TO_A_STRONG_RANDOM_SECRET"
    echo "  BACKEND_CORS_ORIGINS=http://localhost:3000"
    echo "  BACKEND_PORT=8000"
    echo "  OPENROUTER_API_KEY=your-api-key"
    exit 1
fi

# Extract BACKEND_PORT, default to 8000 if not set
BACKEND_PORT=$(grep -E '^BACKEND_PORT=' .env | grep -v '^\s*#' | head -n 1 | cut -d '=' -f2- | sed 's/^["'\'']//; s/["'\'']$//' | xargs)
if [ -z "$BACKEND_PORT" ]; then
    BACKEND_PORT=8000
    echo "BACKEND_PORT not found in .env, using default: $BACKEND_PORT"
fi

echo "Using BACKEND_PORT: $BACKEND_PORT"

# Add host.docker.internal for Windows/Mac to connect to host PostgreSQL
# For Linux, you may need to use --network host or 172.17.0.1
docker run -d \
  --name notebooklm-backend \
  -p "${BACKEND_PORT}:8000" \
  --env-file .env \
  --add-host=host.docker.internal:host-gateway \
  -v "$(pwd)/logs:/app/logs" \
  -v "$(pwd)/outputs:/app/outputs" \
  -v "$(pwd)/uploads:/app/uploads" \
  -v "$(pwd)/qdrant_db:/app/qdrant_db" \
  notebooklm-backend

echo "[OK] Backend container started!"
echo "View logs: docker logs -f notebooklm-backend"
echo "API: http://localhost:$BACKEND_PORT"
echo "Docs: http://localhost:$BACKEND_PORT/docs"
