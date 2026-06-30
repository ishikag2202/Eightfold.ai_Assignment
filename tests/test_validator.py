import sys, os, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.extractors import csv_extractor, json_extractor, github_extractor, pdf_extractor, notes_extractor
from pipeline.merger import merge
from pipeline.projector import project
from pipeline.validator import validate_canonical, validate_projection


def _build_test_profile():
    records = [
        csv_extractor.extract("data/sample_recruiter.csv"),
        json_extractor.extract("data/sample_ats.json"),
        github_extractor.extract("octocat"),
        pdf_extractor.extract("data/sample_resume.pdf"),
        notes_extractor.extract("data/sample_notes.txt"),
    ]
    return merge(records)


def test_validate_canonical_clean_profile():
    profile = _build_test_profile()
    warnings = validate_canonical(profile)
    assert warnings == []


def test_validate_canonical_catches_missing_field():
    broken = {"candidate_id": "123"}
    warnings = validate_canonical(broken)
    assert len(warnings) > 0


def test_validate_projection_passes_for_valid_output():
    profile = _build_test_profile()
    with open("configs/default_config.json") as f:
        config = json.load(f)
    output = project(profile, config)
    errors = validate_projection(output, config)
    assert errors == []


def test_validate_projection_catches_wrong_type():
    config = {"fields": [{"path": "full_name", "type": "number"}]}
    output = {"full_name": "Jane Doe"}  # string, but config says number
    errors = validate_projection(output, config)
    assert len(errors) == 1