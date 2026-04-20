"""
Database Configuration
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os

# Get database URL from environment or use SQLite for development
# TEST_DATABASE_URL overrides DATABASE_URL for test isolation
DATABASE_URL = os.getenv("TEST_DATABASE_URL") or os.getenv(
    "DATABASE_URL",
    "sqlite:///./csr.db"
)

# SQLAlchemy engine configuration
if DATABASE_URL.startswith("sqlite"):
    # For SQLite
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # For PostgreSQL
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        future=True,
    )

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Session:
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    from app.models.models import Base
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")
