import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.extractors import notes_extractor


def test_extract_valid_notes():
    result = notes_extractor.extract("data/sample_notes.txt")
    assert result["_source"] == "notes_txt"
    assert "jane.doe@gmail.com" in result["emails"]
    assert result["links"]["linkedin"] == "https://linkedin.com/in/janedoe-eng"
    assert result["links"]["github"] == "https://github.com/octocat"


def test_extract_finds_known_skills():
    result = notes_extractor.extract("data/sample_notes.txt")
    assert "python" in result["skills"]
    assert "kubernetes" in result["skills"]


def test_extract_years_experience_mentioned():
    result = notes_extractor.extract("data/sample_notes.txt")
    assert result["years_experience_mentioned"] == 6


def test_extract_missing_file():
    result = notes_extractor.extract("data/does_not_exist.txt")
    assert result == {}


def test_extract_no_skills_in_unrelated_text(tmp_path):
    note = tmp_path / "empty_notes.txt"
    note.write_text("Had a nice chat about weekend plans, nothing technical discussed.")
    result = notes_extractor.extract(str(note))
    assert result["skills"] == []
    assert result["emails"] == []