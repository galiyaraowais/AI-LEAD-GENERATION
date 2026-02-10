"""Lead model definition for database persistence."""

# Import datetime for timestamp defaults.
from datetime import datetime
# Import SQLAlchemy column and type tools.
from sqlalchemy import Column, Integer, String, DateTime
# Import declarative base for ORM models.
from sqlalchemy.orm import declarative_base

# Create the base class for ORM models.
Base = declarative_base()


class Lead(Base):
    """ORM model representing a lead record."""

    # Define the table name used in SQLite.
    __tablename__ = "leads"

    # Create an auto-incrementing integer primary key.
    id = Column(Integer, primary_key=True, index=True)
    # Store lead full name as required text.
    name = Column(String(150), nullable=False)
    # Store unique email to prevent duplicates.
    email = Column(String(255), nullable=False, unique=True, index=True)
    # Store phone number text format.
    phone = Column(String(30), nullable=False)
    # Store business type/category as text.
    business_type = Column(String(100), nullable=False)
    # Store lead source such as web/csv/manual.
    source = Column(String(20), nullable=False)
    # Store lifecycle status: New/Qualified/Rejected.
    status = Column(String(20), nullable=False, default="New")
    # Store derived email domain from enrichment.
    email_domain = Column(String(100), nullable=True)
    # Store guessed category from enrichment rules.
    guessed_category = Column(String(100), nullable=True)
    # Store lead score as text for simplicity in this demo.
    lead_score = Column(Integer, nullable=True)
    # Store country guess from phone prefix.
    country = Column(String(100), nullable=True)
    # Store creation timestamp in UTC.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
