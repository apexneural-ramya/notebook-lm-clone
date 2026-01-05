# PowerShell script to run backend using Dockerfile only

Write-Host "Building NotebookLM Backend Docker image..." -ForegroundColor Cyan
docker build -t notebooklm-backend .

Write-Host "Stopping existing container (if any)..." -ForegroundColor Yellow
docker stop notebooklm-backend 2>$null
docker rm notebooklm-backend 2>$null

Write-Host "Starting NotebookLM Backend container..." -ForegroundColor Green
if (-not (Test-Path .env)) {
    Write-Host "Error: .env file not found!" -ForegroundColor Red
    Write-Host "Please create a .env file in the backend directory with required environment variables." -ForegroundColor Yellow
    Write-Host "Example:" -ForegroundColor Yellow
    Write-Host "  DATABASE_URL=postgresql+asyncpg://postgres:postgres@host.docker.internal:5432/notebooklm" -ForegroundColor Gray
    Write-Host "  JWT_SECRET_KEY=your-secret-key" -ForegroundColor Gray
    Write-Host "  BACKEND_CORS_ORIGINS=http://localhost:3002" -ForegroundColor Gray
    Write-Host "  BACKEND_PORT=8007" -ForegroundColor Gray
    Write-Host "  OPENROUTER_API_KEY=your-api-key" -ForegroundColor Gray
    Write-Host "" -ForegroundColor Yellow
    Write-Host "Note: Use 'host.docker.internal' instead of 'localhost' for DATABASE_URL when running in Docker" -ForegroundColor Yellow
    exit 1
}

# Check if PostgreSQL is accessible
Write-Host "Checking database connection..." -ForegroundColor Cyan
$dbUrl = Get-Content .env | Where-Object { $_ -match '^DATABASE_URL=' } | Select-Object -First 1
if ($dbUrl -match 'localhost' -and -not ($dbUrl -match 'host\.docker\.internal')) {
    Write-Host "Warning: DATABASE_URL uses 'localhost'. In Docker, use 'host.docker.internal' to connect to host PostgreSQL." -ForegroundColor Yellow
    Write-Host "Example: DATABASE_URL=postgresql+asyncpg://postgres:postgres@host.docker.internal:5432/notebooklm" -ForegroundColor Gray
}

# Read BACKEND_PORT from .env file (default to 8000)
$portContent = Get-Content .env | Where-Object { 
    $_ -match '^BACKEND_PORT=' -and $_ -notmatch '^\s*#'
} | Select-Object -First 1

if ($portContent) {
    $backendPort = ($portContent -split '=', 2)[1].Trim()
    if ($backendPort -match '^["''](.*)["'']$') {
        $backendPort = $matches[1]
    }
} else {
    $backendPort = "8000"
    Write-Host "BACKEND_PORT not found in .env, using default: $backendPort" -ForegroundColor Yellow
}

Write-Host "Using BACKEND_PORT: $backendPort" -ForegroundColor Gray

# Add host.docker.internal for Windows/Mac to connect to host PostgreSQL
docker run -d `
  --name notebooklm-backend `
  -p "${backendPort}:8000" `
  --env-file .env `
  --add-host=host.docker.internal:host-gateway `
  -v "${PWD}/logs:/app/logs" `
  -v "${PWD}/outputs:/app/outputs" `
  -v "${PWD}/uploads:/app/uploads" `
  -v "${PWD}/qdrant_db:/app/qdrant_db" `
  notebooklm-backend

Write-Host "[OK] Backend container started!" -ForegroundColor Green
Write-Host "View logs: docker logs -f notebooklm-backend" -ForegroundColor Cyan
Write-Host "API: http://localhost:$backendPort" -ForegroundColor Cyan
Write-Host "Docs: http://localhost:$backendPort/docs" -ForegroundColor Cyan
