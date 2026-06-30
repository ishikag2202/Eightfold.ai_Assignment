import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.extractors import json_extractor


def test_extract_valid_json():
    result = json_extractor.extract("data/sample_ats.json")
    assert "Jane" in result["full_name"]
    assert result["_source"] == "ats_json"
    assert len(result["experience"]) == 2
    assert result["experience"][0]["company"] == "Google LLC"


def test_extract_malformed_json(tmp_path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not valid json")
    result = json_extractor.extract(str(bad_file))
    assert result == {}