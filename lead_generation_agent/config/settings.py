"""Application settings module for centralized configuration."""

# Import pathlib to create OS-safe file paths.
from pathlib import Path

# Define the project root folder path based on this file location.
BASE_DIR = Path(__file__).resolve().parent.parent
# Define the path for the SQLite database file in the data folder.
DATABASE_PATH = BASE_DIR / "data" / "leads.db"
# Define the SQLAlchemy database URL using SQLite.
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
# Define the path of the application log file.
LOG_FILE_PATH = BASE_DIR / "data" / "lead_agent.log"
# Define a simple secret key for Flask sessions/forms in local development.
# NOTE: In production, load this from an environment variable.
SECRET_KEY = "replace-this-with-env-secret"
