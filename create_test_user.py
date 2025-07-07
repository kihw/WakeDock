#!/usr/bin/env python3
"""
Create test user for WakeDock authentication
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from wakedock.database.database import get_db_session, init_database
from wakedock.database.models import User
from wakedock.api.auth.password import hash_password
from sqlalchemy.orm import Session

async def create_test_user():
    """Create a test user for authentication testing"""
    
    # Initialize database
    init_database()
    
    # Get database session
    db: Session = next(get_db_session())
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == "admin").first()
        if existing_user:
            print("✅ Test user 'admin' already exists")
            return
        
        # Create test user
        hashed_password = hash_password("admin123")
        
        test_user = User(
            username="admin",
            email="admin@wakedock.com",
            hashed_password=hashed_password,
            full_name="Admin User",
            role="admin",
            is_active=True,
            is_verified=True
        )
        
        db.add(test_user)
        db.commit()
        
        print("✅ Test user created successfully:")
        print("   Username: admin")
        print("   Password: admin123")
        print("   Email: admin@wakedock.com")
        print("   Role: admin")
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(create_test_user())
