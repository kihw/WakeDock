# WakeDock Docker Development Script
# This script starts the full WakeDock environment using Docker Compose

Write-Host "🐳 Starting WakeDock Docker Environment..." -ForegroundColor Green

# Check if we're in the correct directory
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "❌ Error: Please run this script from the WakeDock root directory" -ForegroundColor Red
    exit 1
}

# Check if Docker is running
try {
    docker version | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Create the external network if it doesn't exist
Write-Host "🔗 Creating Docker network..." -ForegroundColor Cyan
docker network create caddy_net 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Network 'caddy_net' created" -ForegroundColor Green
} else {
    Write-Host "ℹ️  Network 'caddy_net' already exists" -ForegroundColor Yellow
}

# Build and start services
Write-Host "🏗️  Building and starting services..." -ForegroundColor Cyan
docker-compose up --build -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start Docker services" -ForegroundColor Red
    exit 1
}

# Wait for services to be ready
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check service health
Write-Host "🔍 Checking service health..." -ForegroundColor Cyan

# Check backend API
try {
    $apiHealth = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
    Write-Host "✅ Backend API is healthy" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Backend API not yet ready" -ForegroundColor Yellow
}

# Check dashboard
try {
    $dashboardResponse = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5
    if ($dashboardResponse.StatusCode -eq 200) {
        Write-Host "✅ Dashboard is accessible" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Dashboard not yet ready" -ForegroundColor Yellow
}

Write-Host "`n🎉 WakeDock Docker Environment Started!" -ForegroundColor Green
Write-Host "🌐 Dashboard: http://localhost:3000" -ForegroundColor Blue
Write-Host "🔧 Backend API: http://localhost:8000" -ForegroundColor Blue
Write-Host "📚 API Docs: http://localhost:8000/docs" -ForegroundColor Blue
Write-Host "🔧 Caddy Admin: http://localhost:2019" -ForegroundColor Blue

Write-Host "`n📋 Default Login Credentials:" -ForegroundColor Yellow
Write-Host "   Email: admin@wakedock.local" -ForegroundColor Gray
Write-Host "   Password: admin123" -ForegroundColor Gray

Write-Host "`n📊 Useful Commands:" -ForegroundColor Yellow
Write-Host "   View logs: docker-compose logs -f" -ForegroundColor Gray
Write-Host "   Stop all: docker-compose down" -ForegroundColor Gray
Write-Host "   Restart: docker-compose restart" -ForegroundColor Gray
Write-Host "   Status: docker-compose ps" -ForegroundColor Gray

# Optional: Show container status
Write-Host "`n📦 Container Status:" -ForegroundColor Cyan
docker-compose ps
