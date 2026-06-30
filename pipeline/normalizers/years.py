from datetime import date


def _parse_yyyy_mm(s):
    if not s:
        return None
    try:
        year, month = s.split("-")
        return int(year), int(month)
    except (ValueError, AttributeError):
        return None


def calculate_years_experience(experience):
    """
    experience: list of dicts with 'start' and 'end' in YYYY-MM format (end may be None = present).
    Returns total years of experience, rounded to 1 decimal, or None if nothing usable.
    """
    if not experience:
        return None

    today = date.today()
    total_months = 0
    counted_any = False

    for job in experience:
        start = _parse_yyyy_mm(job.get("start"))
        if not start:
            continue
        end = _parse_yyyy_mm(job.get("end"))
        end_year, end_month = end if end else (today.year, today.month)
        start_year, start_month = start

        months = (end_year - start_year) * 12 + (end_month - start_month)
        if months > 0:
            total_months += months
            counted_any = True

    if not counted_any:
        return None
    return round(total_months / 12, 1)