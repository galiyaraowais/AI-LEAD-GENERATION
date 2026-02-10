"""Routes for lead APIs, dashboard, and input channels."""

# Import csv for parsing uploaded files.
import csv
# Import io for reading uploaded bytes as text.
import io
# Import datetime to stamp manual CLI entries.
from datetime import datetime

# Import Flask utilities for routing and responses.
from flask import Blueprint, jsonify, request, current_app, render_template, Response, redirect, url_for, flash

# Import lead ORM model.
from models.lead import Lead
# Import DB session factory.
from services.storage import SessionLocal
# Import validation helper.
from services.validation import validate_lead_payload
# Import enrichment helper.
from services.enrichment import enrich_lead
# Import automation helpers.
from services.automation import assign_status, trigger_next_step
# Import CSV export utility.
from utils.csv_export import leads_to_csv

# Create a blueprint for lead-related endpoints.
leads_bp = Blueprint("leads", __name__)


def save_lead(payload: dict):
    """Core workflow for validating, enriching, and saving a lead."""
    # Get shared logger from Flask app context.
    logger = current_app.config["LOGGER"]
    # Open a new database session.
    db = SessionLocal()
    # Start protected block to ensure session cleanup.
    try:
        # Validate incoming payload data.
        is_valid, message = validate_lead_payload(payload)
        # If validation fails, return clear error response.
        if not is_valid:
            # Log validation error event.
            logger.error("Lead rejected: %s", message)
            # Return error payload and HTTP 400.
            return {"error": message}, 400

        # Check for duplicate lead by unique email.
        existing = db.query(Lead).filter(Lead.email == payload["email"]).first()
        # Reject duplicates to prevent repeated lead entries.
        if existing:
            # Log duplicate rejection event.
            logger.warning("Duplicate lead rejected for email=%s", payload["email"])
            # Return duplicate error message.
            return {"error": "Duplicate lead: email already exists"}, 409

        # Enrich lead payload with derived fields.
        enriched = enrich_lead(payload)
        # Assign lifecycle status from automation rules.
        status = assign_status(enriched)
        # Save status in payload before persistence.
        enriched["status"] = status

        # Create ORM object from final payload values.
        lead = Lead(
            name=enriched["name"],
            email=enriched["email"],
            phone=enriched["phone"],
            business_type=enriched["business_type"],
            source=enriched["source"],
            status=enriched["status"],
            email_domain=enriched["email_domain"],
            guessed_category=enriched["guessed_category"],
            lead_score=enriched["lead_score"],
            country=enriched["country"],
        )

        # Add new lead to current DB transaction.
        db.add(lead)
        # Commit transaction to persist lead in database.
        db.commit()
        # Refresh object to load generated ID and timestamps.
        db.refresh(lead)

        # Trigger simulated next-step automation.
        automation_result = trigger_next_step({"status": lead.status, "email": lead.email, "phone": lead.phone})
        # Log successful lead creation lifecycle event.
        logger.info("Lead created id=%s status=%s automation=%s", lead.id, lead.status, automation_result)

        # Return success response object with lead details.
        return {
            "id": lead.id,
            "name": lead.name,
            "email": lead.email,
            "phone": lead.phone,
            "business_type": lead.business_type,
            "source": lead.source,
            "status": lead.status,
            "email_domain": lead.email_domain,
            "guessed_category": lead.guessed_category,
            "lead_score": lead.lead_score,
            "country": lead.country,
            "created_at": lead.created_at.isoformat(),
            "automation": automation_result,
        }, 201
    # Catch all unexpected runtime errors.
    except Exception as exc:
        # Roll back DB transaction on failure.
        db.rollback()
        # Log stack-safe error details to log file.
        logger.exception("Unexpected error while saving lead: %s", exc)
        # Return generic internal server error response.
        return {"error": "Internal server error while creating lead"}, 500
    # Always close the DB session.
    finally:
        # Close session to release DB resources.
        db.close()


@leads_bp.route("/", methods=["GET"])
def dashboard():
    """Render the dashboard page with optional status filter."""
    # Read optional status query value from URL.
    status_filter = request.args.get("status")
    # Open a database session for reading leads.
    db = SessionLocal()
    # Query database within controlled block.
    try:
        # Start a base query for all leads.
        query = db.query(Lead)
        # Apply status filter when provided.
        if status_filter:
            # Narrow query to requested status.
            query = query.filter(Lead.status == status_filter)
        # Execute query sorted by newest first.
        leads = query.order_by(Lead.created_at.desc()).all()
    finally:
        # Close DB session after read operation.
        db.close()
    # Read feedback message from query parameter.
    message = request.args.get("message")
    # Read feedback category from query parameter.
    message_type = request.args.get("message_type", "info")
    # Show message banner when a message exists.
    if message:
        # Push message into Flask flash storage.
        flash(message, message_type)
    # Render HTML template with lead data.
    return render_template("dashboard.html", leads=leads, status_filter=status_filter)


@leads_bp.route("/web-submit", methods=["POST"])
def web_submit():
    """Handle lead submissions from the HTML web form."""
    # Build payload from form fields.
    payload = {
        "name": request.form.get("name", "").strip(),
        "email": request.form.get("email", "").strip(),
        "phone": request.form.get("phone", "").strip(),
        "business_type": request.form.get("business_type", "").strip(),
        "source": "web",
    }
    # Save lead using shared processing pipeline.
    result, status_code = save_lead(payload)
    # Build friendly message for successful lead creation.
    if status_code == 201:
        # Set success message text.
        message = "Lead created successfully"
        # Set message style category.
        message_type = "success"
    else:
        # Set failure message using API error payload.
        message = result.get("error", "Unable to create lead")
        # Set error style category.
        message_type = "error"
    # Redirect back to dashboard with one-time message parameters.
    return redirect(url_for("leads.dashboard", status=request.args.get("status"), message=message, message_type=message_type))


@leads_bp.route("/upload-csv", methods=["POST"])
def upload_csv():
    """Handle CSV upload and create leads in batch."""
    # Get logger for lifecycle events.
    logger = current_app.config["LOGGER"]
    # Check uploaded file exists in request.
    if "file" not in request.files:
        # Return error when file part missing.
        return jsonify({"error": "No file uploaded"}), 400
    # Extract uploaded file object.
    file = request.files["file"]
    # Ensure filename is present.
    if not file.filename:
        # Return error for empty filename.
        return jsonify({"error": "Invalid file"}), 400

    # Read uploaded bytes and decode to UTF-8 text.
    content = file.read().decode("utf-8")
    # Wrap text into StringIO for csv.DictReader.
    stream = io.StringIO(content)
    # Parse CSV rows using header names.
    reader = csv.DictReader(stream)

    # Initialize counters for summary response.
    created_count = 0
    # Store row-specific errors for user feedback.
    errors = []

    # Process each CSV row sequentially.
    for index, row in enumerate(reader, start=1):
        # Build payload mapping with source set to csv.
        payload = {
            "name": (row.get("name") or "").strip(),
            "email": (row.get("email") or "").strip(),
            "phone": (row.get("phone") or "").strip(),
            "business_type": (row.get("business_type") or "").strip(),
            "source": "csv",
        }
        # Save current row lead.
        result, status_code = save_lead(payload)
        # Track successful rows.
        if status_code == 201:
            # Increase success counter.
            created_count += 1
        else:
            # Append user-readable row error.
            errors.append({"row": index, "error": result.get("error", "Unknown error")})

    # Log upload summary details.
    logger.info("CSV upload processed created=%s errors=%s", created_count, len(errors))
    # Detect browser form submission by checking accepted content type.
    accepts_html = "text/html" in request.headers.get("Accept", "")
    # Redirect to dashboard for browser users.
    if accepts_html:
        # Build compact dashboard summary message.
        summary = f"CSV import complete: created={created_count}, errors={len(errors)}"
        # Choose message category based on whether errors were found.
        category = "success" if not errors else "error"
        # Redirect browser back to dashboard with summary banner.
        return redirect(url_for("leads.dashboard", message=summary, message_type=category))

    # Return JSON summary for API-style clients.
    return jsonify({"created": created_count, "errors": errors}), 200


@leads_bp.route("/leads", methods=["POST"])
def create_lead_api():
    """Create a lead through REST API."""
    # Parse incoming JSON payload or default to empty dict.
    payload = request.get_json(silent=True) or {}
    # Auto-set source to api when not provided.
    payload.setdefault("source", "api")
    # Use common save pipeline and capture output.
    result, status_code = save_lead(payload)
    # Return JSON response with status code.
    return jsonify(result), status_code


@leads_bp.route("/leads", methods=["GET"])
def get_leads_api():
    """Return all leads as JSON."""
    # Open database session.
    db = SessionLocal()
    # Query within safe block.
    try:
        # Fetch all leads sorted by newest first.
        leads = db.query(Lead).order_by(Lead.created_at.desc()).all()
        # Convert lead objects into serializable dictionaries.
        data = [
            {
                "id": lead.id,
                "name": lead.name,
                "email": lead.email,
                "phone": lead.phone,
                "business_type": lead.business_type,
                "source": lead.source,
                "status": lead.status,
                "lead_score": lead.lead_score,
                "country": lead.country,
                "created_at": lead.created_at.isoformat(),
                "timestamp": lead.created_at.isoformat(),
            }
            for lead in leads
        ]
    finally:
        # Ensure session closure after query.
        db.close()
    # Return all leads in JSON format.
    return jsonify(data), 200


@leads_bp.route("/leads/search", methods=["GET"])
def search_leads_api():
    """Search leads by status and business type."""
    # Read optional status filter from query params.
    status = request.args.get("status")
    # Read optional business type search from query params.
    business_type = request.args.get("business_type")
    # Open DB session.
    db = SessionLocal()
    # Query with cleanup block.
    try:
        # Start base query object.
        query = db.query(Lead)
        # Apply status filter when provided.
        if status:
            query = query.filter(Lead.status == status)
        # Apply business type partial-match filter.
        if business_type:
            query = query.filter(Lead.business_type.ilike(f"%{business_type}%"))
        # Execute search query.
        leads = query.order_by(Lead.created_at.desc()).all()
    finally:
        # Close DB session.
        db.close()
    # Return serializable JSON results.
    return jsonify([
        {
            "id": lead.id,
            "name": lead.name,
            "email": lead.email,
            "phone": lead.phone,
            "business_type": lead.business_type,
            "source": lead.source,
            "status": lead.status,
            "lead_score": lead.lead_score,
            "country": lead.country,
            "timestamp": lead.created_at.isoformat(),
        }
        for lead in leads
    ]), 200


@leads_bp.route("/health", methods=["GET"])
def health_check():
    """Provide a lightweight health check endpoint for monitoring."""
    # Return simple alive response.
    return jsonify({"status": "ok"}), 200


@leads_bp.route("/leads/<int:lead_id>", methods=["DELETE"])
def delete_lead_api(lead_id: int):
    """Delete lead by ID from database."""
    # Access shared logger for audit trail.
    logger = current_app.config["LOGGER"]
    # Open DB session.
    db = SessionLocal()
    # Perform delete in protected block.
    try:
        # Fetch target lead by ID.
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        # Return not found if no matching lead exists.
        if not lead:
            return jsonify({"error": "Lead not found"}), 404
        # Delete found lead.
        db.delete(lead)
        # Commit deletion transaction.
        db.commit()
        # Log deletion event.
        logger.info("Lead deleted id=%s", lead_id)
        # Return success message.
        return jsonify({"message": "Lead deleted"}), 200
    # Handle unexpected errors.
    except Exception as exc:
        # Rollback transaction on failure.
        db.rollback()
        # Log delete error details.
        logger.exception("Error deleting lead id=%s error=%s", lead_id, exc)
        # Return internal server error response.
        return jsonify({"error": "Internal server error while deleting lead"}), 500
    finally:
        # Close DB session.
        db.close()


@leads_bp.route("/leads/export", methods=["GET"])
def export_leads_csv_api():
    """Export all leads as downloadable CSV."""
    # Open DB session for read-only export.
    db = SessionLocal()
    # Query data and close session safely.
    try:
        # Fetch all leads sorted by oldest first for exports.
        leads = db.query(Lead).order_by(Lead.id.asc()).all()
    finally:
        # Close DB session after data retrieval.
        db.close()

    # Convert lead records to CSV text.
    csv_text = leads_to_csv(leads)
    # Return CSV response with download headers.
    return Response(
        csv_text,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads_export.csv"},
    )


def create_manual_cli_lead(name: str, email: str, phone: str, business_type: str):
    """Allow optional manual lead creation through CLI workflow."""
    # Build payload using manual source indicator.
    payload = {
        "name": name,
        "email": email,
        "phone": phone,
        "business_type": business_type,
        "source": "manual",
        "timestamp": datetime.utcnow().isoformat(),
    }
    # Return save pipeline result tuple.
    return save_lead(payload)
