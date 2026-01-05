#!/bin/bash
# Script to run frontend using Dockerfile only

set -e

if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please create a .env file in the frontend directory with required environment variables."
    echo "Example:"
    echo "  NEXT_PUBLIC_API_URL=http://localhost:8000"
    echo "  FRONTEND_PORT=3000"
    exit 1
fi

# Read NEXT_PUBLIC_API_URL from .env file
# Handle comments and whitespace
if [ -f .env ]; then
    # Extract NEXT_PUBLIC_API_URL, ignoring comments and empty lines
    NEXT_PUBLIC_API_URL=$(grep -E '^NEXT_PUBLIC_API_URL=' .env | grep -v '^\s*#' | head -n 1 | cut -d '=' -f2- | sed 's/^["'\'']//; s/["'\'']$//' | xargs)
    
    if [ -z "$NEXT_PUBLIC_API_URL" ]; then
        echo "Error: NEXT_PUBLIC_API_URL not found or empty in .env file!"
        echo "Please ensure your .env file contains: NEXT_PUBLIC_API_URL=http://localhost:8000"
        exit 1
    fi
    
    # Extract FRONTEND_PORT, default to 3000 if not set
    FRONTEND_PORT=$(grep -E '^FRONTEND_PORT=' .env | grep -v '^\s*#' | head -n 1 | cut -d '=' -f2- | sed 's/^["'\'']//; s/["'\'']$//' | xargs)
    if [ -z "$FRONTEND_PORT" ]; then
        FRONTEND_PORT=3000
        echo "FRONTEND_PORT not found in .env, using default: $FRONTEND_PORT"
    fi
fi

echo "Building NotebookLM Frontend Docker image..."
echo "Using NEXT_PUBLIC_API_URL: $NEXT_PUBLIC_API_URL"
echo "Using FRONTEND_PORT: $FRONTEND_PORT"
docker build -t notebooklm-frontend --build-arg NEXT_PUBLIC_API_URL="$NEXT_PUBLIC_API_URL" .

echo "Stopping existing container (if any)..."
docker stop notebooklm-frontend 2>/dev/null || true
docker rm notebooklm-frontend 2>/dev/null || true

echo "Starting NotebookLM Frontend container..."
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please create a .env file in the frontend directory with required environment variables."
    echo "Example:"
    echo "  NEXT_PUBLIC_API_URL=http://localhost:8000"
    echo "  FRONTEND_PORT=3000"
    exit 1
fi

docker run -d \
  --name notebooklm-frontend \
  -p "${FRONTEND_PORT}:3000" \
  --env-file .env \
  notebooklm-frontend

echo "[OK] Frontend container started!"
echo "View logs: docker logs -f notebooklm-frontend"
echo "Frontend: http://localhost:$FRONTEND_PORT"
