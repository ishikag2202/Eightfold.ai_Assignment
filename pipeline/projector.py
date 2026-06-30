import re
from pipeline.normalizers.phone import normalize_e164
from pipeline.normalizers.skills import canonicalize as canonicalize_skill


def _get_nested(obj, path):
    """
    Resolve a canonical-record path like:
      'full_name'        -> obj['full_name']
      'emails[0]'         -> obj['emails'][0]
      'skills[].name'      -> [s['name'] for s in obj['skills']]
    """
    # array index: e.g. emails[0]
    m = re.match(r'^(\w+)\[(\d+)\]$', path)
    if m:
        key, idx = m.group(1), int(m.group(2))
        arr = obj.get(key) or []
        return arr[idx] if idx < len(arr) else None

    # array map: e.g. skills[].name
    m2 = re.match(r'^(\w+)\[\]\.(\w+)$', path)
    if m2:
        key, subkey = m2.group(1), m2.group(2)
        arr = obj.get(key) or []
        return [item.get(subkey) for item in arr if isinstance(item, dict)]

    # plain field
    return obj.get(path)


def _apply_normalize(value, normalize_type):
    if normalize_type == "E164":
        if isinstance(value, str):
            return normalize_e164(value)
        return value
    if normalize_type == "canonical":
        if isinstance(value, list):
            return [canonicalize_skill(v) for v in value if v]
        if isinstance(value, str):
            return canonicalize_skill(value)
        return value
    return value


def project(canonical, config):
    """
    canonical: the merged canonical profile dict.
    config: dict with "fields" (list of field specs), "include_confidence", "on_missing".
    Returns a new dict shaped per the config. Raises ValueError on required-but-missing fields
    when on_missing == "error".
    """
    on_missing = config.get("on_missing", "null")
    include_confidence = config.get("include_confidence", False)
    result = {}

    for field_spec in config.get("fields", []):
        out_path = field_spec["path"]
        src_path = field_spec.get("from", out_path)
        required = field_spec.get("required", False)
        normalize_type = field_spec.get("normalize")

        value = _get_nested(canonical, src_path)

        if normalize_type:
            value = _apply_normalize(value, normalize_type)

        is_empty = value is None or value == [] or value == ""

        if is_empty:
            if required and on_missing == "error":
                raise ValueError(f"Required field '{out_path}' is missing from canonical record")
            elif on_missing == "omit":
                continue
            else:  # "null" (default)
                result[out_path] = None
        else:
            result[out_path] = value

    if include_confidence:
        result["overall_confidence"] = canonical.get("overall_confidence")
        result["provenance"] = canonical.get("provenance", [])

    return result