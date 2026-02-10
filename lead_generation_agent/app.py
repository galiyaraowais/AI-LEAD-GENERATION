"""Main Flask application entrypoint for the lead generation agent."""

# Import argparse to support optional manual CLI input.
import argparse
# Import os for environment variable usage.
import os

# Import Flask framework class.
from flask import Flask

# Import app settings.
from config.settings import SECRET_KEY, LOG_FILE_PATH
# Import ORM base and model metadata.
from models.lead import Base
# Import lead routes blueprint and manual CLI helper.
from routes.leads import leads_bp, create_manual_cli_lead
# Import DB engine.
from services.storage import engine
# Import logger setup utility.
from utils.logger import setup_logger


def create_app() -> Flask:
    """Application factory used for runtime and tests."""
    # Create Flask app instance.
    app = Flask(__name__)
    # Configure secret key from environment or fallback setting.
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", SECRET_KEY)

    # Ensure data directory exists before logging/database access.
    LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Initialize shared logger and store in app config.
    app.config["LOGGER"] = setup_logger(str(LOG_FILE_PATH))
    # Create database tables if they do not exist.
    Base.metadata.create_all(bind=engine)

    # Register lead routes blueprint.
    app.register_blueprint(leads_bp)

    # Return configured Flask application.
    return app


def run_manual_cli_mode() -> None:
    """Optional CLI flow to add a lead from terminal input."""
    # Print usage heading for CLI mode.
    print("Manual Lead Entry Mode")
    # Read name value from user input.
    name = input("Name: ").strip()
    # Read email value from user input.
    email = input("Email: ").strip()
    # Read phone value from user input.
    phone = input("Phone: ").strip()
    # Read business type from user input.
    business_type = input("Business type: ").strip()

    # Create temporary app context so save pipeline can use Flask current_app.
    app = create_app()
    # Open app context for logger/config access.
    with app.app_context():
        # Save the CLI lead and get response.
        result, status_code = create_manual_cli_lead(name, email, phone, business_type)
    # Print CLI result for user feedback.
    print(f"Status: {status_code}")
    # Print lead result/error details in terminal.
    print(result)


if __name__ == "__main__":
    # Create argument parser for runtime mode selection.
    parser = argparse.ArgumentParser(description="Lead Generation Agent")
    # Add flag to run optional manual CLI mode.
    parser.add_argument("--manual", action="store_true", help="Run manual CLI lead input")
    # Parse command-line arguments.
    args = parser.parse_args()

    # Run manual mode when flag is provided.
    if args.manual:
        run_manual_cli_mode()
    else:
        # Create Flask app for web/API mode.
        app = create_app()
        # Run Flask development server.
        app.run(host="0.0.0.0", port=5000, debug=True)
