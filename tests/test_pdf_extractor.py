import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.extractors import pdf_extractor


def test_extract_valid_pdf():
    result = pdf_extractor.extract("data/sample_resume.pdf")
    assert result["_source"] == "resume_pdf"
    assert "jane.doe@gmail.com" in result["emails"]
    assert result["links"]["github"] == "https://github.com/octocat"


def test_extract_missing_pdf():
    result = pdf_extractor.extract("data/does_not_exist.pdf")
    assert result == {}

def test_extract_headline_has_no_embedded_newline():
    # Regression test: the SUMMARY paragraph in sample_resume.pdf line-wraps
    # mid-sentence in the PDF's text layer ("...backend systems\nat scale."),
    # which previously leaked a literal "\n" into the headline field.
    result = pdf_extractor.extract("data/sample_resume.pdf")
    assert result["headline"] is not None
    assert "\n" not in result["headline"]
    assert result["headline"] == (
        "Senior Software Engineer with 6+ years of experience building "
        "ML infrastructure and backend systems at scale"
    )