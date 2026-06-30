import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.extractors import csv_extractor, json_extractor, github_extractor, pdf_extractor, notes_extractor
from pipeline.merger import merge


def test_merge_all_real_sources():
    records = [
        csv_extractor.extract("data/sample_recruiter.csv"),
        json_extractor.extract("data/sample_ats.json"),
        github_extractor.extract("octocat"),
        pdf_extractor.extract("data/sample_resume.pdf"),
        notes_extractor.extract("data/sample_notes.txt"),
    ]
    profile = merge(records)

    assert profile["full_name"] is not None
    assert len(profile["emails"]) >= 1
    assert len(profile["phones"]) >= 1
    assert profile["source_count"] == 5
    assert 0 < profile["overall_confidence"] <= 1
    print("\n--- MERGED PROFILE ---")
    import json
    print(json.dumps(profile, indent=2))


def test_merge_empty_sources_does_not_crash():
    profile = merge([{}, {}, None])
    assert profile["emails"] == []
    assert profile["phones"] == []
    assert profile["full_name"] is None


def test_merge_deduplicates_same_email_different_case():
    r1 = {"_source": "recruiter_csv", "emails": ["jane@gmail.com"], "phones": [], "skills": []}
    r2 = {"_source": "ats_json", "emails": ["Jane@Gmail.com"], "phones": [], "skills": []}
    profile = merge([r1, r2])
    assert len(profile["emails"]) == 1


def test_merge_logs_name_conflict():
    r1 = {"_source": "recruiter_csv", "full_name": "Jane Doe", "emails": [], "phones": [], "skills": []}
    r2 = {"_source": "ats_json", "full_name": "Janet Doe", "emails": [], "phones": [], "skills": []}
    profile = merge([r1, r2])
    assert len(profile["conflicts"]) == 1
    assert profile["conflicts"][0]["field"] == "full_name"

def test_merge_drops_malformed_email():
    r1 = {"_source": "recruiter_csv", "full_name": "Test", "emails": ["bad@", "not-an-email", "good@example.com"], "phones": [], "skills": []}
    profile = merge([r1])
    assert profile["emails"] == ["good@example.com"]