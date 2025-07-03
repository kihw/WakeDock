# WakeDock Diagnostic Script
# This script helps diagnose common issues with WakeDock setup

Write-Host "🔍 WakeDock Diagnostic Tool" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green

# Check current directory
Write-Host "`n📁 Current Directory Check:" -ForegroundColor Cyan
if (Test-Path "docker-compose.yml") {
    Write-Host "✅ Found docker-compose.yml" -ForegroundColor Green
} else {
    Write-Host "❌ docker-compose.yml not found. Please run from WakeDock root directory." -ForegroundColor Red
    exit 1
}

# Check Docker
Write-Host "`n🐳 Docker Check:" -ForegroundColor Cyan
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker installed: $dockerVersion" -ForegroundColor Green
    
    docker ps | Out-Null
    Write-Host "✅ Docker daemon is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running or not installed" -ForegroundColor Red
    Write-Host "   Please install Docker Desktop and make sure it's running" -ForegroundColor Yellow
}

# Check Docker Compose
Write-Host "`n📦 Docker Compose Check:" -ForegroundColor Cyan
try {
    $composeVersion = docker-compose --version
    Write-Host "✅ Docker Compose installed: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose not found" -ForegroundColor Red
}

# Check Node.js (for local development)
Write-Host "`n📱 Node.js Check:" -ForegroundColor Cyan
try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js installed: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Node.js not found (only needed for local development)" -ForegroundColor Yellow
}

# Check Python (for backend development)
Write-Host "`n🐍 Python Check:" -ForegroundColor Cyan
try {
    $pythonVersion = python --version
    Write-Host "✅ Python installed: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Python not found (only needed for local development)" -ForegroundColor Yellow
}

# Check environment files
Write-Host "`n⚙️  Environment Files Check:" -ForegroundColor Cyan
if (Test-Path ".env") {
    Write-Host "✅ Found .env file" -ForegroundColor Green
    
    # Check key variables
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "WAKEDOCK_API_URL") {
        Write-Host "✅ WAKEDOCK_API_URL configured" -ForegroundColor Green
    } else {
        Write-Host "⚠️  WAKEDOCK_API_URL not found in .env" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  .env file not found. Creating from template..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✅ Created .env from .env.example" -ForegroundColor Green
    } else {
        Write-Host "❌ .env.example not found" -ForegroundColor Red
    }
}

if (Test-Path "dashboard\.env") {
    Write-Host "✅ Found dashboard\.env file" -ForegroundColor Green
} else {
    Write-Host "⚠️  dashboard\.env file not found" -ForegroundColor Yellow
}

# Check ports
Write-Host "`n🔌 Port Check:" -ForegroundColor Cyan
function Test-Port {
    param([int]$Port)
    try {
        $connection = New-Object System.Net.Sockets.TcpClient("localhost", $Port)
        $connection.Close()
        return $true
    }
    catch {
        return $false
    }
}

$ports = @{
    "Backend API" = 8000
    "Dashboard" = 3000
    "Caddy HTTP" = 80
    "Caddy HTTPS" = 443
    "Caddy Admin" = 2019
    "PostgreSQL" = 5432
    "Redis" = 6379
}

foreach ($service in $ports.GetEnumerator()) {
    if (Test-Port $service.Value) {
        Write-Host "✅ Port $($service.Value) ($($service.Key)) is in use" -ForegroundColor Green
    } else {
        Write-Host "⚪ Port $($service.Value) ($($service.Key)) is available" -ForegroundColor Gray
    }
}

# Check running containers
Write-Host "`n📦 Running Containers Check:" -ForegroundColor Cyan
try {
    $containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Out-String
    if ($containers -match "wakedock") {
        Write-Host "✅ WakeDock containers are running:" -ForegroundColor Green
        Write-Host $containers
    } else {
        Write-Host "⚪ No WakeDock containers currently running" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Cannot check container status" -ForegroundColor Red
}

# Check networks
Write-Host "`n🔗 Network Check:" -ForegroundColor Cyan
try {
    $networks = docker network ls --format "table {{.Name}}\t{{.Driver}}" | Out-String
    if ($networks -match "caddy_net") {
        Write-Host "✅ caddy_net network exists" -ForegroundColor Green
    } else {
        Write-Host "⚠️  caddy_net network not found" -ForegroundColor Yellow
        Write-Host "   Run: docker network create caddy_net" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Cannot check network status" -ForegroundColor Red
}

# API Health Check
Write-Host "`n🏥 API Health Check:" -ForegroundColor Cyan
try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
    Write-Host "✅ API is responding and healthy" -ForegroundColor Green
    Write-Host "   Response: $($healthResponse | ConvertTo-Json -Compress)" -ForegroundColor Gray
} catch {
    Write-Host "❌ API health check failed" -ForegroundColor Red
    Write-Host "   URL: http://localhost:8000/health" -ForegroundColor Gray
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Gray
}

# Dashboard Health Check
Write-Host "`n🎨 Dashboard Health Check:" -ForegroundColor Cyan
try {
    $dashboardResponse = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5
    if ($dashboardResponse.StatusCode -eq 200) {
        Write-Host "✅ Dashboard is responding" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Dashboard health check failed" -ForegroundColor Red
    Write-Host "   URL: http://localhost:3000" -ForegroundColor Gray
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Gray
}

Write-Host "`n📋 Diagnostic Summary:" -ForegroundColor Yellow
Write-Host "=====================" -ForegroundColor Yellow
Write-Host "🐳 Docker Environment: .\start-docker.ps1" -ForegroundColor Blue
Write-Host "🖥️  Local Development: .\start-dev.ps1" -ForegroundColor Blue
Write-Host "📚 Documentation: docs/development/SETUP.md" -ForegroundColor Blue
Write-Host "🔧 Troubleshooting: docs/deployment/README.md" -ForegroundColor Blue

Write-Host "`n✅ Diagnostic complete!" -ForegroundColor Green
