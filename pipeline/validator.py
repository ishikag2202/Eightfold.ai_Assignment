def validate_canonical(profile):
    """Sanity-check the internal canonical record. Returns a list of warning strings (empty = clean)."""
    warnings = []
    required_top_level = ["candidate_id", "emails", "phones", "skills", "experience",
                           "education", "provenance", "conflicts", "overall_confidence"]
    for field in required_top_level:
        if field not in profile:
            warnings.append(f"Missing expected field: {field}")

    if not isinstance(profile.get("emails", []), list):
        warnings.append("emails should be a list")
    if not isinstance(profile.get("phones", []), list):
        warnings.append("phones should be a list")

    conf = profile.get("overall_confidence")
    if conf is not None and not (0 <= conf <= 1):
        warnings.append(f"overall_confidence out of range: {conf}")

    return warnings


def validate_projection(output, config):
    """Validate a projected output against its own config's required fields and declared types."""
    errors = []
    type_map = {
        "string": str,
        "string[]": list,
        "number": (int, float),
        "boolean": bool,
    }

    for field_spec in config.get("fields", []):
        path = field_spec["path"]
        required = field_spec.get("required", False)
        declared_type = field_spec.get("type")

        if path not in output or output[path] is None:
            if required and config.get("on_missing") != "omit":
                errors.append(f"Required field '{path}' is missing or null in output")
            continue

        if declared_type and declared_type in type_map:
            expected = type_map[declared_type]
            if not isinstance(output[path], expected):
                errors.append(
                    f"Field '{path}' expected type {declared_type}, got {type(output[path]).__name__}"
                )

    return errors