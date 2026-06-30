import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.confidence import (
    score_field, pick_field_winner, weighted_overall_confidence
)


def test_score_field_ats_no_bonus():
    score = score_field("full_name", "ats_json")
    assert score == 0.95  # 0.95 reliability x 1.0 extraction x 1.0 normalization


def test_score_field_resume_has_extraction_discount():
    score = score_field("emails", "resume_pdf")
    assert score == round(0.85 * 0.95, 2)


def test_agreement_bonus_two_sources():
    score = score_field("full_name", "ats_json", agreeing_source_count=1)
    assert score == round(0.95 + 0.05, 2)


def test_agreement_bonus_three_plus_sources():
    # 0.95 base + 0.10 agreement bonus = 1.05, correctly clamped to 1.0
    score = score_field("full_name", "ats_json", agreeing_source_count=2)
    assert score == 1.0


def test_conflict_penalty():
    score = score_field("full_name", "ats_json", has_conflict=True)
    assert score == round(0.95 - 0.10, 2)


def test_normalization_failure_penalty():
    score = score_field("phones", "ats_json", normalization_succeeded=False)
    assert score == round(0.95 * 0.90, 2)


def test_score_capped_at_one():
    score = score_field("full_name", "ats_json", agreeing_source_count=3)
    assert score == 1.0


def test_pick_field_winner_uses_field_specific_priority():
    candidates = [("Jane Doe", "recruiter_csv"), ("Janet Doe", "resume_pdf")]
    value, source = pick_field_winner("full_name", candidates)
    assert source == "resume_pdf"  # resume ranks higher than csv for full_name


def test_weighted_overall_confidence():
    scores = {"full_name": 0.9, "emails": 0.8, "skills": 0.7}
    result = weighted_overall_confidence(scores)
    assert 0.0 < result < 0.9  # lower than before, since completeness is now factored in


def test_weighted_overall_confidence_thin_profile_scores_low():
    scores = {"full_name": 0.9}
    result = weighted_overall_confidence(scores)
    assert result < 0.3  # one field out of ~7 should score low overall


def test_weighted_overall_confidence_full_profile_scores_high():
    scores = {
        "full_name": 0.9, "emails": 0.9, "phones": 0.9, "experience": 0.9,
        "skills": 0.9, "education": 0.9, "location": 0.9, "links": 0.9,
    }
    result = weighted_overall_confidence(scores)
    assert result > 0.8