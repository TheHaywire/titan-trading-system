import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from pathlib import Path

# Define the database file path
# We place it in the titan_system directory for now, but could be configured elsewhere
DB_DIR = Path(__file__).parent.parent.parent / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "titan.db"

DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create the engine
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}, # Needed for SQLite with multiple threads
    echo=False # Set to True to see SQL queries for debugging
)

# Create a scoped session factory
# This ensures that we have a thread-safe session registry
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# Base class for models
Base = declarative_base()

def get_db():
    """
    Generator function to yield a database session.
    Useful for dependency injection or 'with' contexts.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize the database by creating all tables defined in models.
    """
    # Import all models here to ensure they are registered with Base
    from titan_system.data import models
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at {DB_PATH}")
