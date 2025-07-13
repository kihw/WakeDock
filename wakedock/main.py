"""
Simple FastAPI application for testing the backend build.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import os

app = FastAPI(
    title="WakeDock Backend",
    description="Docker Management API",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "WakeDock Backend is running", "status": "healthy"}

@app.get("/api/v1/health")
async def health():
    return {
        "status": "healthy",
        "service": "wakedock-backend",
        "version": "1.0.0",
        "port": 5000
    }

if __name__ == "__main__":
    uvicorn.run(
        "wakedock.main:app",
        host="0.0.0.0",
        port=5000,
        reload=False
    )
