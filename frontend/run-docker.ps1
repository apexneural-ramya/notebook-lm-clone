# PowerShell script to run frontend using Dockerfile only

if (-not (Test-Path .env)) {
    Write-Host "Error: .env file not found!" -ForegroundColor Red
    Write-Host "Please create a .env file in the frontend directory with required environment variables." -ForegroundColor Yellow
    Write-Host "Example:" -ForegroundColor Yellow
    Write-Host "  NEXT_PUBLIC_API_URL=http://localhost:8000" -ForegroundColor Gray
    Write-Host "  FRONTEND_PORT=3000" -ForegroundColor Gray
    exit 1
}

# Read .env file and extract NEXT_PUBLIC_API_URL
# Handle comments, whitespace, and quoted values
$envContent = Get-Content .env | Where-Object { 
    $_ -match '^NEXT_PUBLIC_API_URL=' -and $_ -notmatch '^\s*#'
} | Select-Object -First 1

if ($envContent) {
    # Extract value, handling quotes and whitespace
    $apiUrl = ($envContent -split '=', 2)[1].Trim()
    # Remove quotes if present
    if ($apiUrl -match '^["''](.*)["'']$') {
        $apiUrl = $matches[1]
    }
} else {
    Write-Host "Error: NEXT_PUBLIC_API_URL not found in .env file!" -ForegroundColor Red
    Write-Host "Please ensure your .env file contains: NEXT_PUBLIC_API_URL=http://localhost:8000" -ForegroundColor Yellow
    exit 1
}

if ([string]::IsNullOrWhiteSpace($apiUrl)) {
    Write-Host "Error: NEXT_PUBLIC_API_URL value is empty in .env file!" -ForegroundColor Red
    exit 1
}

# Read FRONTEND_PORT from .env file (default to 3000)
$portContent = Get-Content .env | Where-Object { 
    $_ -match '^FRONTEND_PORT=' -and $_ -notmatch '^\s*#'
} | Select-Object -First 1

if ($portContent) {
    $frontendPort = ($portContent -split '=', 2)[1].Trim()
    if ($frontendPort -match '^["''](.*)["'']$') {
        $frontendPort = $matches[1]
    }
} else {
    $frontendPort = "3000"
    Write-Host "FRONTEND_PORT not found in .env, using default: $frontendPort" -ForegroundColor Yellow
}

Write-Host "Building NotebookLM Frontend Docker image..." -ForegroundColor Cyan
Write-Host "Using NEXT_PUBLIC_API_URL: $apiUrl" -ForegroundColor Gray
Write-Host "Using FRONTEND_PORT: $frontendPort" -ForegroundColor Gray

# Build with explicit build argument (escape quotes if needed)
$buildArg = "--build-arg NEXT_PUBLIC_API_URL=$apiUrl"
Write-Host "Build command: docker build -t notebooklm-frontend $buildArg ." -ForegroundColor DarkGray
docker build -t notebooklm-frontend --build-arg "NEXT_PUBLIC_API_URL=$apiUrl" .

Write-Host "Stopping existing container (if any)..." -ForegroundColor Yellow
docker stop notebooklm-frontend 2>$null
docker rm notebooklm-frontend 2>$null

Write-Host "Starting NotebookLM Frontend container..." -ForegroundColor Green
if (-not (Test-Path .env)) {
    Write-Host "Error: .env file not found!" -ForegroundColor Red
    Write-Host "Please create a .env file in the frontend directory with required environment variables." -ForegroundColor Yellow
    Write-Host "Example:" -ForegroundColor Yellow
    Write-Host "  NEXT_PUBLIC_API_URL=http://localhost:8000" -ForegroundColor Gray
    Write-Host "  FRONTEND_PORT=3000" -ForegroundColor Gray
    exit 1
}

docker run -d `
  --name notebooklm-frontend `
  -p "${frontendPort}:3000" `
  --env-file .env `
  notebooklm-frontend

Write-Host "[OK] Frontend container started!" -ForegroundColor Green
Write-Host "View logs: docker logs -f notebooklm-frontend" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:$frontendPort" -ForegroundColor Cyan
