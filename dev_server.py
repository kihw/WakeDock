"""
Minimal FastAPI development server for WakeDock
This server provides basic API endpoints for frontend development
"""

from fastapi import FastAPI, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import json
from datetime import datetime, timedelta
import jwt

# Initialize FastAPI app
app = FastAPI(
    title="WakeDock API",
    description="Docker service wake-up and management system",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
SECRET_KEY = "dev-secret-key-change-me-in-production"
ALGORITHM = "HS256"

# Models
class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class Service(BaseModel):
    id: str
    name: str
    image: str
    status: str
    ports: List[dict] = []
    environment: dict = {}
    volumes: List[dict] = []
    created_at: str
    updated_at: str
    health_status: Optional[str] = "unknown"
    restart_policy: str = "unless-stopped"
    labels: dict = {}

class SystemOverview(BaseModel):
    services: dict
    system: dict
    docker: dict

# Mock data
mock_services = [
    {
        "id": "nginx-1",
        "name": "nginx-web",
        "image": "nginx:latest",
        "status": "running",
        "ports": [{"host": 80, "container": 80, "protocol": "tcp"}],
        "environment": {"ENV": "production"},
        "volumes": [],
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "health_status": "healthy",
        "restart_policy": "unless-stopped",
        "labels": {"app": "nginx"}
    },
    {
        "id": "redis-1",
        "name": "redis-cache",
        "image": "redis:alpine",
        "status": "stopped",
        "ports": [{"host": 6379, "container": 6379, "protocol": "tcp"}],
        "environment": {},
        "volumes": [],
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "health_status": "unknown",
        "restart_policy": "unless-stopped",
        "labels": {"app": "redis"}
    }
]

mock_user = {
    "id": "user-1",
    "email": "admin@wakedock.com",
    "name": "Admin User",
    "role": "admin"
}

# Helper functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return email
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# Routes
@app.get("/")
async def root():
    return {"message": "WakeDock API is running", "version": "1.0.0"}

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/v1/auth/token", response_model=LoginResponse)
async def login(username: str = Form(), password: str = Form()):
    # Simple authentication for development - accept both username and email
    if (username == "admin@wakedock.com" or username == "admin") and password == "admin":
        access_token = create_access_token(data={"sub": username})
        return LoginResponse(
            access_token=access_token,
            user=mock_user
        )
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/v1/auth/me")
async def get_current_user(email: str = Depends(verify_token)):
    return mock_user

@app.get("/api/v1/services", response_model=List[Service])
async def get_services(email: str = Depends(verify_token)):
    return mock_services

@app.get("/api/v1/services/{service_id}", response_model=Service)
async def get_service(service_id: str, email: str = Depends(verify_token)):
    service = next((s for s in mock_services if s["id"] == service_id), None)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service

@app.post("/api/v1/services/{service_id}/start")
async def start_service(service_id: str, email: str = Depends(verify_token)):
    service = next((s for s in mock_services if s["id"] == service_id), None)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    service["status"] = "starting"
    return {"message": f"Service {service_id} start initiated"}

@app.post("/api/v1/services/{service_id}/stop")
async def stop_service(service_id: str, email: str = Depends(verify_token)):
    service = next((s for s in mock_services if s["id"] == service_id), None)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    service["status"] = "stopping"
    return {"message": f"Service {service_id} stop initiated"}

@app.post("/api/v1/services/{service_id}/restart")
async def restart_service(service_id: str, email: str = Depends(verify_token)):
    service = next((s for s in mock_services if s["id"] == service_id), None)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    service["status"] = "starting"
    return {"message": f"Service {service_id} restart initiated"}

@app.get("/api/v1/overview", response_model=SystemOverview)
async def get_system_overview(email: str = Depends(verify_token)):
    running_count = sum(1 for s in mock_services if s["status"] == "running")
    stopped_count = sum(1 for s in mock_services if s["status"] == "stopped")
    
    return SystemOverview(
        services={
            "total": len(mock_services),
            "running": running_count,
            "stopped": stopped_count,
            "error": 0
        },
        system={
            "cpu_usage": 45.2,
            "memory_usage": 62.8,
            "disk_usage": 34.1,
            "uptime": 86400
        },
        docker={
            "version": "24.0.0",
            "containers": len(mock_services),
            "images": 15,
            "volumes": 8
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "dev_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
