"""
Simple app entry point for uvicorn.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

def create_application():
    """Create the FastAPI application synchronously."""
    try:
        app = FastAPI(title="WakeDock", version="1.0.0")
        
        # Configure CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, be more specific
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Add a simple health endpoint
        @app.get("/api/v1/health")
        async def health_check():
            return {"status": "healthy", "version": "1.0.0"}
        
        # Add a simple login endpoint for testing
        @app.post("/api/v1/auth/login")
        async def login(form_data: dict):
            # Simple test login - handle form data
            username = form_data.get("username")
            password = form_data.get("password")
            
            if username == "admin" and password == "admin":
                return {
                    "access_token": "test_token_123",
                    "token_type": "bearer",
                    "user": {
                        "id": 1,
                        "username": "admin",
                        "email": "admin@wakedock.com"
                    }
                }
            return {"error": "Invalid credentials"}
        
        # Add a login endpoint that accepts form data
        from fastapi import Form
        @app.post("/api/v1/auth/login-form")
        async def login_form(username: str = Form(), password: str = Form()):
            if username == "admin" and password == "admin":
                return {
                    "access_token": "test_token_123",
                    "token_type": "bearer",
                    "user": {
                        "id": 1,
                        "username": "admin",
                        "email": "admin@wakedock.com"
                    }
                }
            return {"error": "Invalid credentials"}
        
        logger.info("WakeDock application created successfully")
        return app
        
    except Exception as e:
        logger.error(f"Failed to create application: {e}")
        # Return a minimal FastAPI app as fallback
        app = FastAPI(title="WakeDock Fallback", version="1.0.0")
        
        @app.get("/")
        async def root():
            return {"message": "WakeDock is running in fallback mode"}
            
        return app

# Create the app for uvicorn
app = create_application()
