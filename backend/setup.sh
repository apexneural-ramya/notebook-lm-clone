#!/bin/bash
# Setup script for backend authentication

echo "Setting up NotebookLM Backend Authentication..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your database and JWT settings!"
fi

# Install dependencies
echo "Installing dependencies..."
uv sync

# Initialize Alembic if not already done
if [ ! -d "migrations/versions" ]; then
    echo "Initializing Alembic migrations..."
    uv run alembic revision --autogenerate -m "create_users_table"
fi

# Run migrations
echo "Running database migrations..."
uv run alembic upgrade head

echo "✅ Setup complete!"
echo "Run the server with: uv run python run.py"
echo "Or: uv run uvicorn app.api:app --reload --host \$BACKEND_HOST --port \$BACKEND_PORT"

