#!/bin/bash

# WakeDock Deployment Status and Health Check Script
# Comprehensive system status verification

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Icons
SUCCESS="✅"
ERROR="❌"
WARNING="⚠️"
INFO="ℹ️"
LOADING="🔄"

echo -e "${BLUE}WakeDock Deployment Status Check${NC}"
echo "=================================="
echo

# Function to check command existence
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if service is running
check_service_status() {
    local service_name=$1
    local container_name=$2
    
    if docker ps --format "table {{.Names}}" | grep -q "^${container_name}$"; then
        echo -e "${SUCCESS} ${service_name} is running"
        return 0
    else
        echo -e "${ERROR} ${service_name} is not running"
        return 1
    fi
}

# Function to check port accessibility
check_port() {
    local port=$1
    local service=$2
    
    if command_exists nc; then
        if nc -z localhost $port 2>/dev/null; then
            echo -e "${SUCCESS} Port ${port} (${service}) is accessible"
            return 0
        else
            echo -e "${ERROR} Port ${port} (${service}) is not accessible"
            return 1
        fi
    else
        # Fallback using netstat or ss
        if netstat -tuln 2>/dev/null | grep -q ":${port} " || ss -tuln 2>/dev/null | grep -q ":${port} "; then
            echo -e "${SUCCESS} Port ${port} (${service}) is listening"
            return 0
        else
            echo -e "${WARNING} Port ${port} (${service}) status unknown (no nc/netstat/ss)"
            return 1
        fi
    fi
}

# Function to check HTTP endpoint
check_http_endpoint() {
    local url=$1
    local name=$2
    local expected_status=${3:-200}
    
    if command_exists curl; then
        local status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
        if [ "$status_code" = "$expected_status" ]; then
            echo -e "${SUCCESS} ${name} endpoint is healthy (HTTP $status_code)"
            return 0
        else
            echo -e "${ERROR} ${name} endpoint returned HTTP $status_code (expected $expected_status)"
            return 1
        fi
    else
        echo -e "${WARNING} Cannot check ${name} endpoint (curl not available)"
        return 1
    fi
}

# Function to check file existence
check_file() {
    local file_path=$1
    local description=$2
    
    if [ -f "$file_path" ]; then
        echo -e "${SUCCESS} ${description} exists: ${file_path}"
        return 0
    else
        echo -e "${ERROR} ${description} missing: ${file_path}"
        return 1
    fi
}

# Function to check directory
check_directory() {
    local dir_path=$1
    local description=$2
    
    if [ -d "$dir_path" ]; then
        echo -e "${SUCCESS} ${description} exists: ${dir_path}"
        return 0
    else
        echo -e "${ERROR} ${description} missing: ${dir_path}"
        return 1
    fi
}

# Initialize counters
total_checks=0
passed_checks=0

# Function to run check and count results
run_check() {
    total_checks=$((total_checks + 1))
    if "$@"; then
        passed_checks=$((passed_checks + 1))
    fi
}

echo -e "${INFO} Starting system checks...\n"

# 1. Prerequisites Check
echo -e "${BLUE}1. Prerequisites${NC}"
echo "----------------"

run_check command_exists docker && echo -e "${SUCCESS} Docker is installed" || echo -e "${ERROR} Docker is not installed"
run_check command_exists docker-compose && echo -e "${SUCCESS} Docker Compose is installed" || echo -e "${ERROR} Docker Compose is not installed"

# Check Docker daemon
if docker info >/dev/null 2>&1; then
    echo -e "${SUCCESS} Docker daemon is running"
    run_check true
else
    echo -e "${ERROR} Docker daemon is not accessible"
    run_check false
fi

echo

# 2. Configuration Files Check
echo -e "${BLUE}2. Configuration Files${NC}"
echo "----------------------"

run_check check_file "docker-compose.yml" "Docker Compose configuration"
run_check check_file "Dockerfile" "WakeDock Dockerfile"
run_check check_file "requirements.txt" "Python requirements"
run_check check_file "config/config.yml" "WakeDock configuration"
run_check check_file "caddy/Caddyfile" "Caddy configuration"

# Check environment file
if [ -f ".env" ]; then
    echo -e "${SUCCESS} Environment file exists: .env"
    run_check true
else
    echo -e "${WARNING} Environment file missing: .env (using .env.example as reference)"
    run_check false
fi

echo

# 3. Data Directories Check
echo -e "${BLUE}3. Data Directories${NC}"
echo "-------------------"

# Load environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

WAKEDOCK_DATA_DIR=${WAKEDOCK_DATA_DIR:-/Docker/config/wakedock}
CADDY_DATA_DIR=${CADDY_DATA_DIR:-${WAKEDOCK_DATA_DIR}/caddy-data}
CADDY_CONFIG_DIR=${CADDY_CONFIG_DIR:-${WAKEDOCK_DATA_DIR}/caddy-config}

run_check check_directory "$WAKEDOCK_DATA_DIR" "WakeDock data directory"
run_check check_directory "$CADDY_DATA_DIR" "Caddy data directory"
run_check check_directory "$CADDY_CONFIG_DIR" "Caddy config directory"

echo

# 4. Docker Services Check
echo -e "${BLUE}4. Docker Services${NC}"
echo "------------------"

# Check if docker-compose services are running
if [ -f "docker-compose.yml" ]; then
    services=$(docker-compose config --services 2>/dev/null || echo "")
    if [ -n "$services" ]; then
        while IFS= read -r service; do
            if [ -n "$service" ]; then
                container_name=$(docker-compose ps -q "$service" 2>/dev/null | head -1)
                if [ -n "$container_name" ]; then
                    container_name=$(docker inspect --format '{{.Name}}' "$container_name" 2>/dev/null | sed 's/^.//' || echo "")
                fi
                
                if [ -n "$container_name" ]; then
                    run_check check_service_status "$service" "$container_name"
                else
                    echo -e "${ERROR} Service $service is not running"
                    run_check false
                fi
            fi
        done <<< "$services"
    else
        echo -e "${WARNING} Could not read docker-compose services"
        run_check false
    fi
else
    echo -e "${ERROR} docker-compose.yml not found"
    run_check false
fi

echo

# 5. Network Connectivity Check
echo -e "${BLUE}5. Network Connectivity${NC}"
echo "-----------------------"

# Standard WakeDock ports
WAKEDOCK_PORT=${WAKEDOCK_PORT:-8000}
CADDY_HTTP_PORT=${CADDY_HTTP_PORT:-80}
CADDY_HTTPS_PORT=${CADDY_HTTPS_PORT:-443}
DASHBOARD_PORT=${DASHBOARD_PORT:-3000}

run_check check_port "$WAKEDOCK_PORT" "WakeDock API"
run_check check_port "$CADDY_HTTP_PORT" "Caddy HTTP"
run_check check_port "$CADDY_HTTPS_PORT" "Caddy HTTPS"

# Dashboard port (only if dashboard is enabled)
if docker ps --format "table {{.Names}}" | grep -q "dashboard"; then
    run_check check_port "$DASHBOARD_PORT" "Dashboard"
fi

echo

# 6. Health Endpoints Check
echo -e "${BLUE}6. Health Endpoints${NC}"
echo "-------------------"

# WakeDock API health
run_check check_http_endpoint "http://localhost:${WAKEDOCK_PORT}/health" "WakeDock API Health"

# Caddy admin API (if accessible)
if check_port 2019 "Caddy Admin" >/dev/null 2>&1; then
    run_check check_http_endpoint "http://localhost:2019/config/" "Caddy Admin API"
fi

# Dashboard (if running)
if docker ps --format "table {{.Names}}" | grep -q "dashboard"; then
    run_check check_http_endpoint "http://localhost:${DASHBOARD_PORT}" "Dashboard" "200"
fi

echo

# 7. Resource Usage Check
echo -e "${BLUE}7. Resource Usage${NC}"
echo "-----------------"

if command_exists docker; then
    echo -e "${INFO} Docker system information:"
    docker system df 2>/dev/null || echo -e "${WARNING} Could not get Docker system info"
    echo
    
    echo -e "${INFO} Running containers:"
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo -e "${WARNING} Could not list containers"
    echo
fi

echo

# 8. Log Check
echo -e "${BLUE}8. Recent Logs${NC}"
echo "--------------"

if [ -f "docker-compose.yml" ]; then
    echo -e "${INFO} Recent logs from services:"
    docker-compose logs --tail=5 2>/dev/null || echo -e "${WARNING} Could not retrieve logs"
else
    echo -e "${WARNING} Cannot check logs without docker-compose.yml"
fi

echo

# Summary
echo -e "${BLUE}Summary${NC}"
echo "======="

success_rate=$((passed_checks * 100 / total_checks))

echo -e "Total checks: ${total_checks}"
echo -e "Passed: ${GREEN}${passed_checks}${NC}"
echo -e "Failed: ${RED}$((total_checks - passed_checks))${NC}"
echo -e "Success rate: ${success_rate}%"

if [ $success_rate -ge 90 ]; then
    echo -e "\n${SUCCESS} WakeDock deployment is ${GREEN}HEALTHY${NC}"
    exit_code=0
elif [ $success_rate -ge 70 ]; then
    echo -e "\n${WARNING} WakeDock deployment has ${YELLOW}WARNINGS${NC}"
    exit_code=1
else
    echo -e "\n${ERROR} WakeDock deployment has ${RED}CRITICAL ISSUES${NC}"
    exit_code=2
fi

echo
echo -e "${INFO} For detailed troubleshooting, check:"
echo "  - Docker logs: docker-compose logs"
echo "  - System logs: journalctl -u docker"
echo "  - Network: netstat -tulpn"
echo "  - Disk space: df -h"

exit $exit_code
