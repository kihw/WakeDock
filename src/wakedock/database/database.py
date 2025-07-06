"""Database configuration and session management for WakeDock."""

import logging
import os
from typing import Generator, Optional
from contextlib import contextmanager

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.exc import SQLAlchemyError

from ..config import get_settings
from ..performance.database.optimizer import DatabaseOptimizer

logger = logging.getLogger(__name__)

# Create the declarative base for models
Base = declarative_base()


class DatabaseManager:
    """Manages database connections and sessions for WakeDock."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize the database manager.
        
        Args:
            database_url: Database connection URL. If None, will be set when needed.
        """
        self.settings = get_settings()
        self.database_url = database_url
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        self._initialized = False
    
    def _get_database_url(self) -> str:
        """Get database URL from environment or use default SQLite."""
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            return db_url
        
        # Try to use the configured data path first
        try:
            db_path = os.path.join(self.settings.wakedock.data_path, "wakedock.db")
            db_dir = os.path.dirname(db_path)
            os.makedirs(db_dir, exist_ok=True)
            
            # Test if we can write to this location
            test_file = os.path.join(db_dir, '.write_test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            
            return f"sqlite:///{db_path}"
            
        except (PermissionError, OSError) as e:
            # Fallback to a local directory inside the container
            logger.warning("Cannot write to configured data path (%s): %s", self.settings.wakedock.data_path, e)
            logger.warning("This is likely due to Docker volume mount permissions.")
            logger.warning("Using fallback location inside container (data will not persist across container restarts)")
            fallback_dir = "/tmp/wakedock"
            os.makedirs(fallback_dir, exist_ok=True)
            fallback_path = os.path.join(fallback_dir, "wakedock.db")
            logger.info("Using fallback database path: %s", fallback_path)
            return f"sqlite:///{fallback_path}"
    
    def initialize(self) -> None:
        """Initialize database engine and session factory."""
        # Set database URL if not already set
        if not self.database_url:
            self.database_url = self._get_database_url()
        
        if self._initialized:
            return
            
        try:
            # Create engine with appropriate settings
            if self.database_url.startswith("sqlite"):
                # SQLite specific settings
                self.engine = create_engine(
                    self.database_url,
                    connect_args={"check_same_thread": False},
                    echo=self.settings.wakedock.debug
                )
            else:
                # PostgreSQL/MySQL settings with optimization
                self.engine = DatabaseOptimizer.create_optimized_engine(
                    self.database_url,
                    echo=self.settings.wakedock.debug
                )
            
            # Initialize database optimizer
            self.optimizer = DatabaseOptimizer(self.engine)
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            self._initialized = True
            
        except SQLAlchemyError as e:
            raise RuntimeError(f"Failed to initialize database: {e}")
    
    def create_tables(self) -> None:
        """Create all database tables."""
        if not self._initialized:
            self.initialize()
            
        if not self.engine:
            raise RuntimeError("Database engine not initialized")
        
        try:
            Base.metadata.create_all(bind=self.engine)
        except SQLAlchemyError as e:
            raise RuntimeError(f"Failed to create tables: {e}")
    
    def drop_tables(self) -> None:
        """Drop all database tables."""
        if not self._initialized:
            self.initialize()
            
        if not self.engine:
            raise RuntimeError("Database engine not initialized")
        
        try:
            Base.metadata.drop_all(bind=self.engine)
        except SQLAlchemyError as e:
            raise RuntimeError(f"Failed to drop tables: {e}")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup."""
        if not self._initialized:
            self.initialize()
        
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_optimizer(self) -> Optional[DatabaseOptimizer]:
        """Get the database optimizer instance."""
        if not self._initialized:
            self.initialize()
        return getattr(self, 'optimizer', None)
    
    def get_performance_stats(self) -> dict:
        """Get database performance statistics."""
        optimizer = self.get_optimizer()
        if optimizer:
            return optimizer.get_performance_stats()
        return {}


# Global database manager instance (lazy initialization)
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager  
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_db_session() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions."""
    db_manager = get_db_manager()
    with db_manager.get_session() as session:
        yield session


async def get_async_db_session() -> Generator[Session, None, None]:
    """FastAPI dependency for async database sessions (wrapper for compatibility)."""
    db_manager = get_db_manager()
    with db_manager.get_session() as session:
        yield session


def init_database() -> None:
    """Initialize the database for the application."""
    db_manager = get_db_manager()
    db_manager.initialize()
    db_manager.create_tables()
    
    # Seed default data
    _seed_default_data()


def _seed_default_data() -> None:
    """Seed the database with default data."""
    from .models import User, UserRole
    from ..api.auth.password import hash_password
    from ..config import get_settings
    
    settings = get_settings()
    
    with get_db_manager().get_session() as session:
        # Check if admin user already exists
        admin_user = session.query(User).filter(
            (User.username == 'admin') | (User.email == 'admin@wakedock.com')
        ).first()
        
        if not admin_user:
            # Create default admin user
            hashed_password = hash_password(settings.wakedock.admin_password)
            admin_user = User(
                username='admin',
                email='admin@wakedock.com',
                hashed_password=hashed_password,
                full_name='Default Administrator',
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True
            )
            
            session.add(admin_user)
            session.commit()
            logger.info("Default admin user created successfully")
        else:
            logger.info("Admin user already exists, skipping creation")
