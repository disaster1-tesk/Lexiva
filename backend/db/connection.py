"""
Database Connection and Session Management
SQLite with SQLAlchemy
"""
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = "sqlite:///./data/database.db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base for models
Base = declarative_base()


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    logger.info("Initializing database...")
    
    # Import all models to create tables
    from models import User, Conversation, Word, Pronunciation, Writing, Statistics, AISettings
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("✓ Database tables created")


# Initialize on import
if __name__ != "__main__":
    try:
        os.makedirs("data", exist_ok=True)
        logger.info("Database directory ready: data/")
        init_db()
    except Exception as e:
        logger.error(f"Database init failed: {e}")