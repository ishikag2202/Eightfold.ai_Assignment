import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.extractors import csv_extractor


def test_extract_valid_csv():
    result = csv_extractor.extract("data/sample_recruiter.csv")
    assert result["full_name"] == "Jane Doe"
    assert result["emails"] == ["jane.doe@gmail.com"]
    assert result["_source"] == "recruiter_csv"


def test_extract_missing_file():
    result = csv_extractor.extract("data/does_not_exist.csv")
    assert result == {}