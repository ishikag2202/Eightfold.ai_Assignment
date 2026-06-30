import sys, os, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.extractors import csv_extractor, json_extractor, github_extractor, pdf_extractor, notes_extractor
from pipeline.merger import merge
from pipeline.projector import project


def _build_test_profile():
    records = [
        csv_extractor.extract("data/sample_recruiter.csv"),
        json_extractor.extract("data/sample_ats.json"),
        github_extractor.extract("octocat"),
        pdf_extractor.extract("data/sample_resume.pdf"),
        notes_extractor.extract("data/sample_notes.txt"),
    ]
    return merge(records)


def test_project_with_default_config():
    profile = _build_test_profile()
    with open("configs/default_config.json") as f:
        config = json.load(f)

    result = project(profile, config)

    assert result["full_name"] == "Jane Doe"
    assert result["primary_email"] == "jane.doe@gmail.com"
    assert result["phone"] == "+14155550192"
    assert isinstance(result["skills"], list)
    assert "overall_confidence" in result
    print("\n--- PROJECTED OUTPUT (default config) ---")
    print(json.dumps(result, indent=2))


def test_project_omit_missing():
    profile = _build_test_profile()
    config = {
        "fields": [
            {"path": "twitter_handle", "from": "nonexistent_field"},  # guaranteed absent
        ],
        "on_missing": "omit",
    }
    result = project(profile, config)
    assert "twitter_handle" not in result


def test_project_error_on_missing_required():
    profile = _build_test_profile()
    config = {
        "fields": [
            {"path": "twitter_handle", "from": "nonexistent_field", "required": True},
        ],
        "on_missing": "error",
    }
    try:
        project(profile, config)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_project_excludes_confidence_when_disabled():
    profile = _build_test_profile()
    config = {
        "fields": [{"path": "full_name"}],
        "include_confidence": False,
    }
    result = project(profile, config)
    assert "overall_confidence" not in result