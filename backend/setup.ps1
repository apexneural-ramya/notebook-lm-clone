# PowerShell setup script for backend authentication

Write-Host "Setting up NotebookLM Backend Authentication..." -ForegroundColor Green

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "⚠️  Please edit .env with your database and JWT settings!" -ForegroundColor Yellow
}

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Cyan
uv sync

# Initialize Alembic if not already done
if (-not (Test-Path "migrations\versions")) {
    Write-Host "Initializing Alembic migrations..." -ForegroundColor Cyan
    uv run alembic revision --autogenerate -m "create_users_table"
}

# Run migrations
Write-Host "Running database migrations..." -ForegroundColor Cyan
uv run alembic upgrade head

Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host "Run the server with: uv run python run.py" -ForegroundColor Cyan
Write-Host "Or: uv run uvicorn app.api:app --reload --host `$env:BACKEND_HOST --port `$env:BACKEND_PORT" -ForegroundColor Cyan

