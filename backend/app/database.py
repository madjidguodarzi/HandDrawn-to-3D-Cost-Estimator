# backend/app/database.py
"""
Database configuration and session management for the application.
Handles SQLAlchemy engine creation, session generation, and table initialization.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from typing import Generator
from backend.app.models import Base
from backend.app.core.config import settings
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = settings.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite in multi-threaded environments
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator:
    """
    Dependency function that yields a database session.
    Ensures the session is properly closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initializes the database by creating all tables defined in the models.
    This should be called once at application startup.
    """
    try:
        from backend.app.models import Project, Wall, Room, CostItem  # noqa: F401
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created or verified successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise