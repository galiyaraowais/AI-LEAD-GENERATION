"""Automation logic for lead lifecycle and follow-up simulation."""

# Import Dict for typed payload operations.
from typing import Dict


def assign_status(lead_payload: Dict) -> str:
    """Assign lead status based on basic quality rules."""
    # Reject lead when validation source marked an error flag.
    if lead_payload.get("invalid"):
        # Return rejected status for invalid leads.
        return "Rejected"
    # Qualify lead when score is high enough.
    if lead_payload.get("lead_score", 0) >= 80:
        # Return qualified status for strong leads.
        return "Qualified"
    # Otherwise keep lead as new for manual follow-up.
    return "New"


def trigger_next_step(lead_payload: Dict) -> str:
    """Simulate downstream action such as email or WhatsApp."""
    # Read source and status for branching decisions.
    status = lead_payload.get("status", "New")
    # For qualified leads, simulate priority email sequence.
    if status == "Qualified":
        # Return a simulation message for email automation.
        return f"Email simulation triggered for {lead_payload['email']}"
    # For new leads, simulate WhatsApp reminder flow.
    if status == "New":
        # Return a simulation message for WhatsApp automation.
        return f"WhatsApp simulation queued for {lead_payload['phone']}"
    # For rejected leads, no action is taken.
    return "No automation triggered"
