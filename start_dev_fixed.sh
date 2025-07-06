#!/bin/bash

# WakeDock Development Startup Script with Proper Configuration

set -e

echo "🚀 Starting WakeDock Development Environment"
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=8000
FRONTEND_PORT=3001
API_URL="http://195.201.199.226:8000"

echo -e "${BLUE}📋 Configuration:${NC}"
echo -e "   Backend API: ${API_URL}"
echo -e "   Frontend: http://195.201.199.226:${FRONTEND_PORT}"
echo -e "   API Docs: ${API_URL}/api/docs"
echo ""

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1
    else
        return 0
    fi
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=0
    
    echo -e "${YELLOW}⏳ Waiting for ${name} to be ready...${NC}"
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ ${name} is ready!${NC}"
            return 0
        fi
        
        attempt=$((attempt + 1))
        echo -e "${YELLOW}   Attempt ${attempt}/${max_attempts}...${NC}"
        sleep 2
    done
    
    echo -e "${RED}❌ ${name} failed to start within timeout${NC}"
    return 1
}

# Stop any existing processes
echo -e "${YELLOW}🛑 Stopping any existing processes...${NC}"
pkill -f "uvicorn.*wakedock" || true
pkill -f "vite.*wakedock" || true
sleep 2

# Create test user
echo -e "${BLUE}👤 Creating test user...${NC}"
if python3 create_test_user.py; then
    echo -e "${GREEN}✅ Test user setup complete${NC}"
else
    echo -e "${YELLOW}⚠️  Test user setup failed or user already exists${NC}"
fi

# Start backend
echo -e "${BLUE}🔧 Starting Backend API Server...${NC}"
if ! check_port $BACKEND_PORT; then
    echo -e "${RED}❌ Port ${BACKEND_PORT} is already in use${NC}"
    exit 1
fi

# Set environment variables for backend
export WAKEDOCK_HOST="0.0.0.0"
export WAKEDOCK_PORT="$BACKEND_PORT"
export WAKEDOCK_LOG_LEVEL="debug"
export CORS_ORIGINS="http://195.201.199.226:3000,http://195.201.199.226:3001,http://localhost:3000,http://localhost:3001"

# Start backend in background
nohup python3 -m uvicorn wakedock.main:app \
    --host 0.0.0.0 \
    --port $BACKEND_PORT \
    --reload \
    --reload-dir src \
    --log-level debug \
    > backend.log 2>&1 &

BACKEND_PID=$!
echo -e "${GREEN}✅ Backend started with PID: ${BACKEND_PID}${NC}"

# Wait for backend to be ready
if ! wait_for_service "${API_URL}/api/v1/health" "Backend API"; then
    echo -e "${RED}❌ Backend failed to start${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Start frontend
echo -e "${BLUE}🎨 Starting Frontend Dashboard...${NC}"
cd dashboard

if ! check_port $FRONTEND_PORT; then
    echo -e "${RED}❌ Port ${FRONTEND_PORT} is already in use${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Set environment variables for frontend
export VITE_API_BASE_URL="$API_URL"
export PUBLIC_API_URL="$API_URL"
export PUBLIC_WS_URL="ws://195.201.199.226:8000/ws"
export NODE_ENV="development"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
    npm install --legacy-peer-deps
fi

# Start frontend in background
nohup npm run dev -- --host 0.0.0.0 --port $FRONTEND_PORT > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✅ Frontend started with PID: ${FRONTEND_PID}${NC}"

cd ..

# Wait for frontend to be ready
if ! wait_for_service "http://195.201.199.226:${FRONTEND_PORT}" "Frontend Dashboard"; then
    echo -e "${RED}❌ Frontend failed to start${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 WakeDock Development Environment Started Successfully!${NC}"
echo -e "${GREEN}=================================================${NC}"
echo ""
echo -e "${BLUE}📱 Frontend Dashboard:${NC} http://195.201.199.226:${FRONTEND_PORT}"
echo -e "${BLUE}🔧 Backend API:${NC} ${API_URL}"
echo -e "${BLUE}📚 API Documentation:${NC} ${API_URL}/api/docs"
echo ""
echo -e "${BLUE}👤 Test User Credentials:${NC}"
echo -e "   Username: admin"
echo -e "   Password: admin123"
echo ""
echo -e "${YELLOW}📋 Process IDs:${NC}"
echo -e "   Backend PID: ${BACKEND_PID}"
echo -e "   Frontend PID: ${FRONTEND_PID}"
echo ""
echo -e "${YELLOW}📄 Log Files:${NC}"
echo -e "   Backend: backend.log"
echo -e "   Frontend: frontend.log"
echo ""
echo -e "${BLUE}🛑 To stop the services:${NC}"
echo -e "   kill ${BACKEND_PID} ${FRONTEND_PID}"
echo ""

# Save PIDs for easy cleanup
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid

# Wait for user interrupt
echo -e "${YELLOW}Press Ctrl+C to stop all services...${NC}"
trap 'echo -e "\n${YELLOW}🛑 Shutting down services...${NC}"; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; rm -f .backend.pid .frontend.pid; exit 0' INT

wait
