from dateutil import parser as date_parser


def normalize_yyyy_mm(raw):
    """Convert any date-like string into YYYY-MM format, or None if unparseable."""
    if raw is None or raw == "":
        return None
    try:
        dt = date_parser.parse(str(raw), default=date_parser.parse("2000-01-01"))
        return dt.strftime("%Y-%m")
    except (date_parser.ParserError, ValueError, TypeError, OverflowError):
        return None