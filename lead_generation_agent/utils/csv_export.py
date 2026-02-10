"""CSV export helper for lead records."""

# Import csv for writing comma-separated values.
import csv
# Import io for in-memory text streams.
import io
# Import Iterable typing for flexible input.
from typing import Iterable


def leads_to_csv(leads: Iterable) -> str:
    """Convert lead ORM objects to CSV text."""
    # Create an in-memory string stream to hold CSV content.
    output = io.StringIO()
    # Create CSV writer object bound to string stream.
    writer = csv.writer(output)

    # Write CSV header row for exported columns.
    writer.writerow([
        "id",
        "name",
        "email",
        "phone",
        "business_type",
        "source",
        "status",
        "email_domain",
        "guessed_category",
        "lead_score",
        "country",
        "created_at",
    ])

    # Loop through each lead and write row values.
    for lead in leads:
        # Write one CSV row for current lead object.
        writer.writerow([
            lead.id,
            lead.name,
            lead.email,
            lead.phone,
            lead.business_type,
            lead.source,
            lead.status,
            lead.email_domain,
            lead.guessed_category,
            lead.lead_score,
            lead.country,
            lead.created_at,
        ])

    # Return the full CSV text result.
    return output.getvalue()
