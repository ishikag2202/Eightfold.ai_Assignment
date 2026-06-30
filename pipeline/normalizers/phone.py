import phonenumbers


def normalize_e164(raw, default_region="US"):
    """Convert any phone string into E.164 format, or None if invalid."""
    if not raw:
        return None
    try:
        parsed = phonenumbers.parse(str(raw), default_region)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
    except phonenumbers.NumberParseException:
        pass
    return None


def get_region(e164_number):
    """Given an E.164 number, return its ISO country code (e.g. 'US')."""
    if not e164_number:
        return None
    try:
        parsed = phonenumbers.parse(e164_number, None)
        return phonenumbers.region_code_for_number(parsed)
    except phonenumbers.NumberParseException:
        return None