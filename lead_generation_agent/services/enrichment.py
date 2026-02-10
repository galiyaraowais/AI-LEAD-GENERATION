"""Lead enrichment logic with simple rule-based simulation."""

# Import Dict for clear typing.
from typing import Dict


def detect_email_domain(email: str) -> str:
    """Extract domain from an email address."""
    # Split email by @ and return right side domain.
    return email.split("@")[-1].lower()


def guess_business_category(business_type: str) -> str:
    """Guess category from business type using simple keyword rules."""
    # Normalize text to lowercase for easier keyword matching.
    value = business_type.lower()
    # Match common keywords to broad categories.
    if any(token in value for token in ["tech", "software", "it", "saas"]):
        # Return technology category.
        return "Technology"
    # Match retail and commerce terms.
    if any(token in value for token in ["shop", "ecommerce", "retail", "store"]):
        # Return retail category.
        return "Retail"
    # Match service-related terms.
    if any(token in value for token in ["agency", "consult", "service", "marketing"]):
        # Return services category.
        return "Services"
    # Return fallback category for unmatched input.
    return "General"


def assign_lead_score(email_domain: str, category: str) -> int:
    """Assign a simple lead score using deterministic rules."""
    # Start from a neutral base score.
    score = 50
    # Boost score when lead is from a business domain.
    if email_domain not in ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]:
        # Add score points for business-like email domain.
        score += 20
    # Boost categories that are often good B2B fit.
    if category in ["Technology", "Services"]:
        # Add points for preferred categories.
        score += 20
    # Return final score capped at 100.
    return min(score, 100)


def country_from_phone(phone: str) -> str:
    """Guess country from phone code using mock rules."""
    # Check common international prefixes and map to country names.
    if phone.startswith("+1"):
        # Return country label for +1 region.
        return "USA/Canada"
    if phone.startswith("+44"):
        # Return country label for UK prefix.
        return "United Kingdom"
    if phone.startswith("+91"):
        # Return country label for India prefix.
        return "India"
    if phone.startswith("+61"):
        # Return country label for Australia prefix.
        return "Australia"
    # Return unknown when prefix is not recognized.
    return "Unknown"


def enrich_lead(payload: Dict) -> Dict:
    """Return payload with enrichment fields added."""
    # Detect email domain from the lead email field.
    domain = detect_email_domain(payload["email"])
    # Guess broader category from business type field.
    category = guess_business_category(payload["business_type"])
    # Compute lead score using domain and category rules.
    score = assign_lead_score(domain, category)
    # Infer mock country from phone prefix.
    country = country_from_phone(payload["phone"])

    # Add derived values back into payload for storage.
    payload["email_domain"] = domain
    # Save guessed category value.
    payload["guessed_category"] = category
    # Save computed lead score.
    payload["lead_score"] = score
    # Save guessed country.
    payload["country"] = country
    # Return enriched payload dictionary.
    return payload
