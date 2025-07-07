"""Configuration routes for frontend runtime config."""

from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()


@router.get("/v1/config")
async def get_frontend_config() -> Dict[str, Any]:
    """Get frontend runtime configuration."""
    return {
        "apiUrl": "/api/v1",
        "wsUrl": "/ws",
        "isDevelopment": False,
        "enableDebug": False,
        "features": {
            "analytics": True,
            "notifications": True,
            "realTimeUpdates": True
        }
    }
