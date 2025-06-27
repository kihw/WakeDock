# WakeDock Management Script for Windows PowerShell

param(
    [string]$Command = "help"
)

# Colors
$ErrorColor = "Red"
$SuccessColor = "Green"
$WarningColor = "Yellow"
$InfoColor = "Cyan"

function Write-Header {
    Write-Host "================================================" -ForegroundColor $InfoColor
    Write-Host "🐳 WakeDock Management Script" -ForegroundColor $InfoColor
    Write-Host "================================================" -ForegroundColor $InfoColor
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor $SuccessColor
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️ $Message" -ForegroundColor $WarningColor
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor $ErrorColor
}

function Test-Requirements {
    Write-Header
    Write-Host "Checking requirements..."
    
    try {
        docker --version | Out-Null
    }
    catch {
        Write-Error "Docker is not installed or not in PATH"
        exit 1
    }
    
    try {
        docker-compose --version | Out-Null
    }
    catch {
        Write-Error "Docker Compose is not installed or not in PATH"
        exit 1
    }
    
    Write-Success "Requirements check passed"
}

function Initialize-Environment {
    if (-not (Test-Path ".env")) {
        Write-Warning ".env file not found"
        if (Test-Path ".env.example") {
            Write-Host "Copying .env.example to .env..."
            Copy-Item ".env.example" ".env"
            Write-Success "Created .env file from example"
            Write-Warning "Please edit .env file with your configuration"
        }
        else {
            Write-Error ".env.example not found"
            exit 1
        }
    }
    else {
        Write-Success ".env file exists"
    }
}

function New-DataDirectories {
    Write-Host "Creating data directories..."
    
    # Load environment variables
    if (Test-Path ".env") {
        Get-Content ".env" | ForEach-Object {
            if ($_ -match "^([^#][^=]+)=(.*)$") {
                [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
            }
        }
    }
    
    # Create directories with defaults
    $dataDir = if ($env:WAKEDOCK_DATA_DIR) { $env:WAKEDOCK_DATA_DIR } else { "./data" }
    $directories = @(
        $dataDir,
        $(if ($env:WAKEDOCK_CORE_DATA) { $env:WAKEDOCK_CORE_DATA } else { "$dataDir/wakedock-core" }),
        $(if ($env:WAKEDOCK_LOGS_DIR) { $env:WAKEDOCK_LOGS_DIR } else { "$dataDir/logs" }),
        $(if ($env:WAKEDOCK_CONFIG_DIR) { $env:WAKEDOCK_CONFIG_DIR } else { "$dataDir/config" }),
        $(if ($env:CADDY_DATA_DIR) { $env:CADDY_DATA_DIR } else { "$dataDir/caddy-data" }),
        $(if ($env:CADDY_CONFIG_DIR) { $env:CADDY_CONFIG_DIR } else { "$dataDir/caddy-config" }),
        $(if ($env:CADDY_CONFIG_VOLUME) { $env:CADDY_CONFIG_VOLUME } else { "$dataDir/caddy-volume" }),
        $(if ($env:DASHBOARD_DATA_DIR) { $env:DASHBOARD_DATA_DIR } else { "$dataDir/dashboard" }),
        $(if ($env:POSTGRES_DATA_DIR) { $env:POSTGRES_DATA_DIR } else { "$dataDir/postgres" }),
        $(if ($env:REDIS_DATA_DIR) { $env:REDIS_DATA_DIR } else { "$dataDir/redis" })
    )
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    
    # Setup initial Caddy configuration
    $caddyConfigPath = if ($env:CADDY_CONFIG_VOLUME) { $env:CADDY_CONFIG_VOLUME } else { "$dataDir/caddy-volume" }
    if (-not (Test-Path "$caddyConfigPath/Caddyfile")) {
        if (Test-Path "./caddy/Caddyfile.auto") {
            Copy-Item "./caddy/Caddyfile.auto" "$caddyConfigPath/Caddyfile" -Force
            Write-Success "Initial Caddyfile created"
        }
    }
    
    Write-Success "Data directories created"
}

function Build-Images {
    Write-Host "Building Docker images..."
    docker-compose build
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Images built successfully"
    }
    else {
        Write-Error "Failed to build images"
        exit 1
    }
}

function Start-Development {
    Write-Host "Starting WakeDock in development mode..."
    New-DockerNetwork
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
    if ($LASTEXITCODE -eq 0) {
        Write-Success "WakeDock development environment started"
        Write-Host ""
        Write-Host "Services available at:" -ForegroundColor $InfoColor
        $dashboardPort = if ($env:DASHBOARD_PORT) { $env:DASHBOARD_PORT } else { "3000" }
        $corePort = if ($env:WAKEDOCK_CORE_PORT) { $env:WAKEDOCK_CORE_PORT } else { "8000" }
        $adminPort = if ($env:CADDY_ADMIN_PORT) { $env:CADDY_ADMIN_PORT } else { "2019" }
        $postgresPort = if ($env:POSTGRES_PORT) { $env:POSTGRES_PORT } else { "5432" }
        $redisPort = if ($env:REDIS_PORT) { $env:REDIS_PORT } else { "6379" }
        
        Write-Host "🌐 Dashboard: http://localhost:$dashboardPort"
        Write-Host "🔧 API: http://localhost:$corePort"
        Write-Host "⚙️ Caddy Admin: http://localhost:$adminPort"
        Write-Host "📊 PostgreSQL: localhost:$postgresPort"
        Write-Host "🔴 Redis: localhost:$redisPort"
    }
    else {
        Write-Error "Failed to start development environment"
        exit 1
    }
}

function Start-Production {
    Write-Host "Starting WakeDock in production mode..."
    New-DockerNetwork
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    if ($LASTEXITCODE -eq 0) {
        Write-Success "WakeDock production environment started"
        Write-Host ""
        Write-Host "Services available at:" -ForegroundColor $InfoColor
        $dashboardPort = if ($env:DASHBOARD_PORT) { $env:DASHBOARD_PORT } else { "3000" }
        $corePort = if ($env:WAKEDOCK_CORE_PORT) { $env:WAKEDOCK_CORE_PORT } else { "8000" }
        
        Write-Host "🌐 Dashboard: http://localhost:$dashboardPort"
        Write-Host "🔧 API: http://localhost:$corePort"
    }
    else {
        Write-Error "Failed to start production environment"
        exit 1
    }
}

function Stop-Services {
    Write-Host "Stopping WakeDock services..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
    Write-Success "Services stopped"
}

function Show-Logs {
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f
}

function Show-Status {
    Write-Host "WakeDock Services Status:" -ForegroundColor $InfoColor
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml ps
}

function New-DockerNetwork {
    # Load environment variables first
    if (Test-Path ".env") {
        Get-Content ".env" | ForEach-Object {
            if ($_ -match "^([^#][^=]+)=(.*)$") {
                [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
            }
        }
    }
    
    $networkName = if ($env:WAKEDOCK_NETWORK) { $env:WAKEDOCK_NETWORK } else { "caddy_net" }
    
    Write-Host "Checking Docker network '$networkName'..."
    
    try {
        $existingNetwork = docker network ls --filter "name=$networkName" --format "{{.Name}}" 2>$null
        if ($existingNetwork -eq $networkName) {
            Write-Success "Docker network '$networkName' already exists"
        }
        else {
            Write-Host "Creating Docker network '$networkName'..."
            docker network create $networkName
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Docker network '$networkName' created successfully"
            }
            else {
                Write-Warning "Failed to create network '$networkName', but continuing..."
            }
        }
    }
    catch {
        Write-Warning "Could not check/create Docker network, but continuing..."
    }
}

# Main script logic
switch ($Command.ToLower()) {
    "setup" {
        Test-Requirements
        Initialize-Environment
        New-DataDirectories
        Build-Images
        New-DockerNetwork
        Write-Success "WakeDock setup completed!"
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor $InfoColor
        Write-Host "1. Edit .env file with your configuration"
        Write-Host "2. Run '.\manage.ps1 dev' to start development environment"
        Write-Host "3. Run '.\manage.ps1 prod' to start production environment"
    }
    "dev" {
        Test-Requirements
        Initialize-Environment
        New-DataDirectories
        Start-Development
    }
    "prod" {
        Test-Requirements
        Initialize-Environment
        New-DataDirectories
        Start-Production
    }
    "stop" {
        Stop-Services
    }
    "logs" {
        Show-Logs
    }
    "status" {
        Show-Status
    }
    "build" {
        Build-Images
    }
    "reset" {
        Write-Warning "This will stop all services and remove all data!"
        $confirmation = Read-Host "Are you sure? (y/N)"
        if ($confirmation.ToLower() -eq "y") {
            Stop-Services
            docker-compose down -v
            if (Test-Path "./data") {
                Remove-Item -Recurse -Force "./data"
            }
            Write-Success "WakeDock reset completed"
        }
    }
    default {
        Write-Header
        Write-Host "Usage: .\manage.ps1 <command>" -ForegroundColor $InfoColor
        Write-Host ""
        Write-Host "Commands:" -ForegroundColor $InfoColor
        Write-Host "  setup  - Initial setup (create .env, directories, build images)"
        Write-Host "  dev    - Start development environment"
        Write-Host "  prod   - Start production environment"
        Write-Host "  stop   - Stop all services"
        Write-Host "  logs   - Show logs (follow mode)"
        Write-Host "  status - Show services status"
        Write-Host "  build  - Build Docker images"
        Write-Host "  reset  - Reset everything (destructive!)"
        Write-Host ""
        Write-Host "Examples:" -ForegroundColor $InfoColor
        Write-Host "  .\manage.ps1 setup    # First time setup"
        Write-Host "  .\manage.ps1 dev      # Start development"
        Write-Host "  .\manage.ps1 logs     # View logs"
        Write-Host "  .\manage.ps1 stop     # Stop services"
    }
}
