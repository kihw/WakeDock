# WakeDock Dashboard Management Script for Windows
# Provides convenient commands for development and deployment

param(
    [string]$Command = "help",
    [string]$Option = ""
)

# Colors for output
$Colors = @{
    Red    = "Red"
    Green  = "Green"
    Yellow = "Yellow"
    Blue   = "Blue"
    White  = "White"
}

# Helper functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Colors.Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Colors.Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Colors.Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Colors.Red
}

function Show-Help {
    @"
WakeDock Dashboard Management Script

Usage: .\manage.ps1 <command> [options]

Commands:
  setup               Set up development environment
  dev                 Start development server
  build               Build for production
  test                Run tests
  test-watch          Run tests in watch mode
  test-coverage       Run tests with coverage
  lint                Run linting
  lint-fix            Fix linting issues
  format              Format code
  type-check          Run TypeScript type checking
  clean               Clean build artifacts and dependencies
  docker-build        Build Docker image
  docker-dev          Start development with Docker
  docker-prod         Start production with Docker
  docker-test         Run tests in Docker
  docker-clean        Clean Docker resources
  deploy-staging      Deploy to staging
  deploy-prod         Deploy to production
  health              Check application health
  logs                Show application logs
  backup              Backup application data
  update              Update dependencies
  security            Run security audit
  help                Show this help message

Examples:
  .\manage.ps1 setup              # Set up development environment
  .\manage.ps1 dev                # Start development server
  .\manage.ps1 test-coverage      # Run tests with coverage report
  .\manage.ps1 docker-build       # Build production Docker image

Environment Variables:
  NODE_ENV            Set environment (development|production|test)
  API_URL            Set API URL for development
  DOCKER_TAG         Set Docker image tag

For more information, see README.md and DEPLOYMENT.md
"@
}

# Check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check Node.js
    try {
        $nodeVersion = (node --version) -replace 'v', ''
        $requiredVersion = [version]"18.0.0"
        $currentVersion = [version]$nodeVersion
        
        if ($currentVersion -lt $requiredVersion) {
            Write-Error "Node.js version $nodeVersion is too old. Please install Node.js 18+ first."
            exit 1
        }
        Write-Info "Node.js version $nodeVersion detected"
    }
    catch {
        Write-Error "Node.js is not installed. Please install Node.js 18+ first."
        exit 1
    }
    
    # Check npm
    try {
        $npmVersion = npm --version
        Write-Info "npm version $npmVersion detected"
    }
    catch {
        Write-Error "npm is not installed."
        exit 1
    }
    
    # Check Docker (optional)
    try {
        $dockerVersion = docker --version
        Write-Info "Docker is available: $dockerVersion"
    }
    catch {
        Write-Warning "Docker is not installed (optional for local development)"
    }
    
    Write-Success "Prerequisites check passed"
}

# Setup development environment
function Invoke-Setup {
    Write-Info "Setting up development environment..."
    
    Test-Prerequisites
    
    # Install dependencies
    Write-Info "Installing dependencies..."
    npm ci
    
    # Copy environment file if it doesn't exist
    if (-not (Test-Path ".env")) {
        Write-Info "Creating .env file from template..."
        Copy-Item ".env.example" ".env"
        Write-Warning "Please update .env with your configuration"
    }
    
    # Create directories
    $directories = @("logs", "test-results", "coverage")
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    
    Write-Success "Development environment setup complete"
    Write-Info "Next steps:"
    Write-Info "1. Update .env with your configuration"
    Write-Info "2. Run '.\manage.ps1 dev' to start development server"
}

# Start development server
function Start-Dev {
    Write-Info "Starting development server..."
    Test-Prerequisites
    
    if (-not (Test-Path ".env")) {
        Write-Warning ".env file not found. Creating from template..."
        Copy-Item ".env.example" ".env"
    }
    
    npm run dev
}

# Build for production
function Invoke-Build {
    Write-Info "Building for production..."
    Test-Prerequisites
    
    # Run type checking first
    npm run type-check
    
    # Run tests
    npm run test:run
    
    # Build
    npm run build
    
    Write-Success "Production build complete"
}

# Run tests
function Invoke-Test {
    param([string]$Type = "run")
    
    Write-Info "Running tests..."
    Test-Prerequisites
    
    switch ($Type) {
        "watch" { npm run test:watch }
        "coverage" { npm run test:coverage }
        default { npm run test:run }
    }
}

# Run linting
function Invoke-Lint {
    param([boolean]$Fix = $false)
    
    Write-Info "Running linting..."
    Test-Prerequisites
    
    if ($Fix) {
        npm run lint:fix
    }
    else {
        npm run lint
    }
}

# Format code
function Invoke-Format {
    Write-Info "Formatting code..."
    Test-Prerequisites
    
    npm run format
}

# Type checking
function Invoke-TypeCheck {
    Write-Info "Running TypeScript type checking..."
    Test-Prerequisites
    
    npm run type-check
}

# Clean build artifacts
function Invoke-Clean {
    param([string]$Type = "")
    
    Write-Info "Cleaning build artifacts and dependencies..."
    
    # Remove build artifacts
    $buildDirs = @("build", ".svelte-kit", "dist", "coverage", "test-results")
    foreach ($dir in $buildDirs) {
        if (Test-Path $dir) {
            Remove-Item -Recurse -Force $dir
            Write-Info "Removed $dir"
        }
    }
    
    # Remove node_modules if requested
    if ($Type -eq "all") {
        if (Test-Path "node_modules") {
            Remove-Item -Recurse -Force "node_modules"
            Write-Info "Removed node_modules"
        }
        if (Test-Path "package-lock.json") {
            Remove-Item -Force "package-lock.json"
            Write-Info "Removed package-lock.json"
        }
    }
    
    # Clean Docker resources if requested
    if ($Type -eq "docker") {
        Invoke-DockerClean
    }
    
    Write-Success "Cleanup complete"
}

# Docker operations
function Invoke-DockerBuild {
    param([string]$Dockerfile = "Dockerfile.prod")
    
    Write-Info "Building Docker image..."
    
    $tag = if ($env:DOCKER_TAG) { $env:DOCKER_TAG } else { "wakedock-dashboard:latest" }
    
    docker build -f $Dockerfile -t $tag .
    Write-Success "Docker image built: $tag"
}

function Start-DockerDev {
    Write-Info "Starting development environment with Docker..."
    
    docker-compose -f docker-compose.dev.yml up -d
    Write-Success "Development environment started"
    Write-Info "Dashboard: http://localhost:3000"
    Write-Info "Use '.\manage.ps1 logs' to view logs"
}

function Start-DockerProd {
    Write-Info "Starting production environment with Docker..."
    
    docker-compose -f docker-compose.yml up -d
    Write-Success "Production environment started"
}

function Invoke-DockerTest {
    Write-Info "Running tests in Docker..."
    
    docker-compose -f docker-compose.dev.yml run --rm test-runner npm run test:run
}

function Invoke-DockerClean {
    Write-Info "Cleaning Docker resources..."
    
    # Stop and remove containers
    try {
        docker-compose -f docker-compose.yml down -v 2>$null
        docker-compose -f docker-compose.dev.yml down -v 2>$null
    }
    catch {
        # Ignore errors if containers don't exist
    }
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes
    docker volume prune -f
    
    Write-Success "Docker resources cleaned"
}

# Health check
function Test-Health {
    Write-Info "Checking application health..."
    
    $url = if ($env:HEALTH_URL) { $env:HEALTH_URL } else { "http://localhost:3000/health" }
    
    try {
        $response = Invoke-WebRequest -Uri $url -Method Get -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Success "Application is healthy"
        }
        else {
            Write-Error "Application health check failed with status: $($response.StatusCode)"
        }
    }
    catch {
        Write-Error "Application health check failed: $($_.Exception.Message)"
    }
}

# Show logs
function Show-Logs {
    param([string]$Service = "dashboard")
    
    $containerName = "wakedock-$Service"
    
    try {
        $containers = docker ps --format "{{.Names}}"
        if ($containers -contains $containerName) {
            docker logs -f $containerName
        }
        else {
            $logFile = "logs\$Service.log"
            if (Test-Path $logFile) {
                Get-Content $logFile -Tail 50 -Wait
            }
            else {
                Write-Error "No logs found for service: $Service"
            }
        }
    }
    catch {
        Write-Error "Failed to show logs: $($_.Exception.Message)"
    }
}

# Backup data
function Invoke-Backup {
    Write-Info "Creating backup..."
    
    $backupDir = "backups\$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    
    # Backup database
    try {
        $containers = docker ps --format "{{.Names}}"
        if ($containers -contains "wakedock-postgres") {
            docker exec wakedock-postgres pg_dump -U wakedock wakedock | Out-File "$backupDir\database.sql"
        }
    }
    catch {
        Write-Warning "Failed to backup database: $($_.Exception.Message)"
    }
    
    # Backup configuration
    if (Test-Path "config") {
        Copy-Item -Recurse "config" "$backupDir\" 2>$null
    }
    if (Test-Path ".env") {
        Copy-Item ".env" "$backupDir\" 2>$null
    }
    
    Write-Success "Backup created: $backupDir"
}

# Update dependencies
function Invoke-Update {
    Write-Info "Updating dependencies..."
    
    # Update npm dependencies
    npm update
    
    # Run security audit
    try {
        npm audit fix
    }
    catch {
        Write-Warning "Some security issues remain"
    }
    
    # Update Docker images
    try {
        docker-compose pull 2>$null
    }
    catch {
        # Ignore if docker-compose is not available
    }
    
    Write-Success "Dependencies updated"
}

# Security audit
function Invoke-Security {
    Write-Info "Running security audit..."
    
    # npm audit
    npm audit
    
    # Check for outdated dependencies
    try {
        npm outdated
    }
    catch {
        # npm outdated returns non-zero when packages are outdated
    }
    
    Write-Info "Security audit complete"
}

# Main command handler
switch ($Command.ToLower()) {
    "setup" { Invoke-Setup }
    "dev" { Start-Dev }
    "build" { Invoke-Build }
    "test" { Invoke-Test }
    "test-watch" { Invoke-Test "watch" }
    "test-coverage" { Invoke-Test "coverage" }
    "lint" { Invoke-Lint }
    "lint-fix" { Invoke-Lint -Fix $true }
    "format" { Invoke-Format }
    "type-check" { Invoke-TypeCheck }
    "clean" { Invoke-Clean $Option }
    "docker-build" { Invoke-DockerBuild $Option }
    "docker-dev" { Start-DockerDev }
    "docker-prod" { Start-DockerProd }
    "docker-test" { Invoke-DockerTest }
    "docker-clean" { Invoke-DockerClean }
    "health" { Test-Health }
    "logs" { Show-Logs $Option }
    "backup" { Invoke-Backup }
    "update" { Invoke-Update }
    "security" { Invoke-Security }
    default { Show-Help }
}
