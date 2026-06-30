import re

# Minimal US-state-to-country mapping; extend as needed.
US_STATE_CODES = {
    "CA", "NY", "TX", "WA", "MA", "IL", "FL", "GA", "PA", "OH",
    "NC", "MI", "NJ", "VA", "CO", "AZ", "OR", "MN", "WI", "MD",
}


def normalize_location(raw):
    """
    raw: a string like 'San Francisco, CA, USA' or a GitHub-style 'San Francisco, CA'.
    Returns {city, region, country} with best-effort parsing, or None if unparseable.
    """
    if not raw:
        return None

    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if not parts:
        return None

    city = parts[0] if len(parts) >= 1 else None
    region = parts[1] if len(parts) >= 2 else None
    country = None

    if len(parts) >= 3:
        country_raw = parts[2].upper()
        country = "US" if country_raw in ("USA", "US", "UNITED STATES") else country_raw
    elif region and region.upper() in US_STATE_CODES:
        country = "US"

    return {"city": city, "region": region, "country": country}