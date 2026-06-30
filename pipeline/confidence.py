SOURCE_RELIABILITY = {
    "ats_json": 0.95,
    "github_api": 0.92,
    "recruiter_csv": 0.90,
    "resume_pdf": 0.85,
    "notes_txt": 0.70,
}

EXTRACTION_CONFIDENCE = {
    "ats_json": 1.00,
    "recruiter_csv": 1.00,
    "github_api": 1.00,
    "resume_pdf": 0.95,
    "notes_txt": 0.80,
}

FIELD_SOURCE_PRIORITY = {
    "full_name":  ["github_api", "recruiter_csv", "resume_pdf", "ats_json"],
    "emails":     ["resume_pdf", "recruiter_csv", "ats_json"],
    "phones":     ["resume_pdf", "recruiter_csv", "ats_json"],
    "skills":     ["notes_txt", "resume_pdf", "github_api", "ats_json"],
    "experience": ["ats_json", "resume_pdf"],
    "education":  ["ats_json", "resume_pdf"],
    "location":   ["resume_pdf", "ats_json"],
    "headline":   ["resume_pdf", "github_api", "ats_json", "recruiter_csv", "notes_txt"],
}

FIELD_WEIGHTS = {
    "full_name": 0.20,
    "emails": 0.15,
    "phones": 0.15,
    "experience": 0.20,
    "skills": 0.15,
    "education": 0.10,
    "location": 0.025,
    "links": 0.025,
}

AGREEMENT_BONUS_2 = 0.05
AGREEMENT_BONUS_3PLUS = 0.10
CONFLICT_PENALTY = 0.10
NORMALIZATION_FAILURE_PENALTY = 0.10


def field_priority_rank(field_name, source):
    """Returns this source's rank for a given field (-1 if not in that field's priority list)."""
    plist = FIELD_SOURCE_PRIORITY.get(field_name, [])
    return plist.index(source) if source in plist else -1


def pick_field_winner(field_name, candidates):
    """
    candidates: list of (value, source) tuples for this field.
    Returns (winning_value, winning_source) using the field-specific priority order.
    Sources not listed for this field rank below all listed sources (rank -1),
    never above them — being unlisted should never accidentally win.
    """
    best_value, best_source, best_rank = None, None, -2
    for value, source in candidates:
        if not value:
            continue
        rank = field_priority_rank(field_name, source)
        if rank > best_rank:
            best_value, best_source, best_rank = value, source, rank
    return best_value, best_source


def score_field(field_name, winning_source, agreeing_source_count=0,
                 has_conflict=False, normalization_succeeded=True):
    """
    Implements: (reliability x extraction_confidence x normalization_confidence)
                + agreement_bonus - conflict_penalty, clamped to [0, 1].
    """
    if winning_source not in SOURCE_RELIABILITY:
        return 0.5

    reliability = SOURCE_RELIABILITY[winning_source]
    extraction_conf = EXTRACTION_CONFIDENCE.get(winning_source, 0.8)
    normalization_conf = 1.0 if normalization_succeeded else (1.0 - NORMALIZATION_FAILURE_PENALTY)

    score = reliability * extraction_conf * normalization_conf

    if agreeing_source_count >= 2:
        score += AGREEMENT_BONUS_3PLUS
    elif agreeing_source_count == 1:
        score += AGREEMENT_BONUS_2

    if has_conflict:
        score -= CONFLICT_PENALTY

    return round(max(0.0, min(1.0, score)), 2)

def weighted_overall_confidence(field_confidence_map):
    """
    field_confidence_map: dict like {"full_name": 0.9, "emails": 0.85, ...}
    Combines (a) how trustworthy the populated fields are, with
    (b) how much of the expected profile is actually populated —
    a thin profile should never score as high as a complete one,
    even if the few fields it has are individually reliable.
    """
    total_weight = 0.0
    weighted_sum = 0.0
    for field, conf in field_confidence_map.items():
        if conf is None:
            continue
        w = FIELD_WEIGHTS.get(field, 0.05)
        weighted_sum += conf * w
        total_weight += w

    if total_weight == 0:
        return 0.0

    trust_score = weighted_sum / total_weight

    # Completeness: what fraction of the total possible field weight is populated
    full_weight = sum(FIELD_WEIGHTS.values())
    completeness = total_weight / full_weight if full_weight else 0.0

    final_score = trust_score * completeness
    return round(max(0.0, min(1.0, final_score)), 2)