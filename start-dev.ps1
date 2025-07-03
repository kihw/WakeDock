# WakeDock Development Startup Script
# This script starts both the backend API server and the frontend dashboard

Write-Host "🚀 Starting WakeDock Development Environment..." -ForegroundColor Green

# Check if we're in the correct directory
if (-not (Test-Path "dev_server.py")) {
    Write-Host "❌ Error: Please run this script from the WakeDock root directory" -ForegroundColor Red
    exit 1
}

# Function to check if a port is in use
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

# Check if ports are available
Write-Host "🔍 Checking ports..." -ForegroundColor Yellow

if (Test-Port 8000) {
    Write-Host "⚠️  Port 8000 is already in use. Please stop the existing process." -ForegroundColor Yellow
}

if (Test-Port 3000) {
    Write-Host "⚠️  Port 3000 is already in use. Please stop the existing process." -ForegroundColor Yellow
}

# Start backend API server
Write-Host "🔧 Starting Backend API Server (Port 8000)..." -ForegroundColor Cyan

$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    python dev_server.py
}

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Check if backend started successfully
if (Test-Port 8000) {
    Write-Host "✅ Backend API Server started successfully on http://localhost:8000" -ForegroundColor Green
    Write-Host "📚 API Documentation: http://localhost:8000/api/docs" -ForegroundColor Blue
}
else {
    Write-Host "❌ Failed to start Backend API Server" -ForegroundColor Red
    Write-Host "💡 Make sure Python and required packages are installed:" -ForegroundColor Yellow
    Write-Host "   pip install fastapi uvicorn pydantic pyjwt" -ForegroundColor Gray
    exit 1
}

# Start frontend dashboard
Write-Host "🎨 Starting Frontend Dashboard (Port 3000)..." -ForegroundColor Cyan

$frontendJob = Start-Job -ScriptBlock {
    Set-Location "$using:PWD\dashboard"
    npm run dev
}

# Wait a moment for frontend to start
Start-Sleep -Seconds 5

# Check if frontend started successfully
if (Test-Port 3000) {
    Write-Host "✅ Frontend Dashboard started successfully on http://localhost:3000" -ForegroundColor Green
}
else {
    Write-Host "❌ Failed to start Frontend Dashboard" -ForegroundColor Red
    Write-Host "💡 Make sure Node.js and dependencies are installed:" -ForegroundColor Yellow
    Write-Host "   cd dashboard && npm install" -ForegroundColor Gray
}

Write-Host "`n🎉 WakeDock Development Environment is ready!" -ForegroundColor Green
Write-Host "🌐 Frontend: http://localhost:3000" -ForegroundColor Blue
Write-Host "🔧 Backend API: http://localhost:8000" -ForegroundColor Blue
Write-Host "📚 API Docs: http://localhost:8000/api/docs" -ForegroundColor Blue
Write-Host "`n📋 Default Login Credentials:" -ForegroundColor Yellow
Write-Host "   Email: admin@wakedock.com" -ForegroundColor Gray
Write-Host "   Password: admin123" -ForegroundColor Gray
Write-Host "`n⚠️  Press Ctrl+C to stop all services" -ForegroundColor Yellow

# Wait for user to press Ctrl+C
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
}
finally {
    Write-Host "`n🛑 Stopping development servers..." -ForegroundColor Yellow
    
    # Stop background jobs
    if ($backendJob) {
        Stop-Job $backendJob -ErrorAction SilentlyContinue
        Remove-Job $backendJob -ErrorAction SilentlyContinue
    }
    
    if ($frontendJob) {
        Stop-Job $frontendJob -ErrorAction SilentlyContinue
        Remove-Job $frontendJob -ErrorAction SilentlyContinue
    }
    
    Write-Host "✅ Development environment stopped." -ForegroundColor Green
}
