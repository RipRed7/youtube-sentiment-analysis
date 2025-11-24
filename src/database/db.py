"""Database connection management (Synchronous SQLAlchemy)"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from dotenv import load_dotenv
import os

# Load .env file automatically
load_dotenv()  # By default, it looks for a .env in current working directory

from src.database.models import Base

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Convert postgres:// to postgresql:// if needed (Neon compatibility)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create synchronous engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=5,
    max_overflow=10,
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions
    
    Usage:
        @app.get("/users")
        def get_users(db: Session = Depends(get_session)):
            return db.query(User).all()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db_session() -> Session:
    """
    Get a database session for manual use (Streamlit)
    
    Usage:
        db = get_db_session()
        try:
            user = db.query(User).filter_by(email="test@example.com").first()
        finally:
            db.close()
    """
    return SessionLocal()


def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")


def drop_all_tables():
    """Drop all tables (DANGER - use only in development)"""
    Base.metadata.drop_all(bind=engine)
    print("⚠️  All tables dropped")