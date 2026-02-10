"""Database storage service using SQLAlchemy."""

# Import SQLAlchemy helpers for engine and sessions.
from sqlalchemy import create_engine
# Import session maker factory for DB sessions.
from sqlalchemy.orm import sessionmaker
# Import settings for DB URL.
from config.settings import DATABASE_URL

# Create a SQLAlchemy engine connected to SQLite.
engine = create_engine(DATABASE_URL, echo=False, future=True)
# Create a session factory for creating DB sessions on demand.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
