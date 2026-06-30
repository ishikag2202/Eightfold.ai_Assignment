import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.extractors import github_extractor


def test_extract_real_user():
    result = github_extractor.extract("octocat")
    assert result["_source"] == "github_api"
    assert result["links"]["github"] == "https://github.com/octocat"


def test_extract_nonexistent_user():
    result = github_extractor.extract("this-user-should-not-exist-zzz999")
    assert result == {}


def test_extract_empty_username():
    result = github_extractor.extract("")
    assert result == {}