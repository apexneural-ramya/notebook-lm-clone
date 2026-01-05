# PowerShell script to validate .env file before running Docker

$envFile = ".env"

if (-not (Test-Path $envFile)) {
    Write-Host "❌ Error: .env file not found in $(Get-Location)" -ForegroundColor Red
    Write-Host "Please create a .env file with required environment variables." -ForegroundColor Yellow
    exit 1
}

Write-Host "🔍 Validating .env file..." -ForegroundColor Cyan

$missingVars = @()

# Check DATABASE_PASSWORD
$dbPassword = Get-Content $envFile | Where-Object { $_ -match '^DATABASE_PASSWORD=' } | Select-Object -First 1
if (-not $dbPassword -or $dbPassword -match '^DATABASE_PASSWORD=$' -or $dbPassword -match 'CHANGE_THIS_PASSWORD') {
    $missingVars += "DATABASE_PASSWORD"
}

# Check JWT_SECRET_KEY
$jwtSecret = Get-Content $envFile | Where-Object { $_ -match '^JWT_SECRET_KEY=' } | Select-Object -First 1
if (-not $jwtSecret -or $jwtSecret -match '^JWT_SECRET_KEY=$' -or $jwtSecret -match 'CHANGE_THIS_TO_A_STRONG_RANDOM_SECRET') {
    $missingVars += "JWT_SECRET_KEY"
}

if ($missingVars.Count -gt 0) {
    Write-Host "❌ Error: Missing or using placeholder values for required variables:" -ForegroundColor Red
    foreach ($var in $missingVars) {
        Write-Host "   - $var" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Please update your .env file with actual values:" -ForegroundColor Yellow
    Write-Host "  - DATABASE_PASSWORD: Set a strong database password" -ForegroundColor Yellow
    Write-Host "  - JWT_SECRET_KEY: Generate with: openssl rand -hex 32" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ .env file validation passed!" -ForegroundColor Green
Write-Host "   All required variables are set." -ForegroundColor Green

