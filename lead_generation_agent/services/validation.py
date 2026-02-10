"""Validation and cleaning helpers for lead data."""

# Import regex for phone validation.
import re
# Import Dict type hint for clarity.
from typing import Dict, Tuple
# Import email validator package for robust email checks.
from email_validator import validate_email, EmailNotValidError


def validate_lead_payload(payload: Dict) -> Tuple[bool, str]:
    """Validate required lead fields and return (is_valid, message)."""
    # Define required input fields for every lead source.
    required_fields = ["name", "email", "phone", "business_type", "source"]
    # Iterate through each required field to check presence and value.
    for field in required_fields:
        # Reject payload if field is missing or empty.
        if not payload.get(field):
            # Return validation failure with a beginner-friendly message.
            return False, f"Missing required field: {field}"

    # Validate accepted source values to keep data consistent.
    allowed_sources = {"web", "csv", "manual", "api"}
    # Reject unknown source values.
    if payload.get("source") not in allowed_sources:
        # Return error when source is not recognized.
        return False, f"Invalid source: expected one of {sorted(allowed_sources)}"

    # Try validating email structure using email-validator package.
    try:
        # Validate and normalize the email address.
        validation_result = validate_email(payload["email"], check_deliverability=False)
        # Replace input email with normalized format (lowercased domain, etc.).
        payload["email"] = validation_result.email
    # Catch invalid email formatting errors.
    except EmailNotValidError as exc:
        # Return invalid status and detailed reason.
        return False, f"Invalid email format: {exc}"

    # Remove spaces and dashes to normalize phone checks.
    normalized_phone = re.sub(r"[\s\-()]+", "", payload["phone"])
    # Keep leading + but verify remaining characters are digits.
    if normalized_phone.startswith("+"):
        # Split out the sign for digit length checks.
        digit_part = normalized_phone[1:]
    else:
        # Use full normalized string when no plus sign exists.
        digit_part = normalized_phone

    # Ensure phone contains only digits after normalization.
    if not digit_part.isdigit():
        # Return error for invalid phone content.
        return False, "Invalid phone number: use digits and optional + sign"

    # Ensure phone length is between 7 and 15 digits (common global range).
    if len(digit_part) < 7 or len(digit_part) > 15:
        # Return error for invalid phone length.
        return False, "Invalid phone number length: expected 7 to 15 digits"

    # Save normalized phone back to payload for consistent storage.
    payload["phone"] = normalized_phone
    # Return successful validation.
    return True, "Valid lead payload"
