import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.normalizers.skills import canonicalize, deduplicate

def test_canonicalize_acronym_languages_not_title_cased():
    # Regression test: these come from GitHub's repo.get("language") values
    # (Linguist names) and would previously fall through to .title(), which
    # mangles acronyms -- e.g. "css".title() == "Css", not "CSS".
    assert canonicalize("css") == "CSS"
    assert canonicalize("Css") == "CSS"
    assert canonicalize("html") == "HTML"
    assert canonicalize("Html") == "HTML"
    assert canonicalize("tex") == "TeX"


def test_canonicalize():
    assert canonicalize("pytorch") == "PyTorch"
    assert canonicalize("PYTORCH") == "PyTorch"
    assert canonicalize("ml") == "Machine Learning"
    assert canonicalize("Some Random Skill") == "Some Random Skill"


def test_deduplicate():
    raw = ["python", "Python", "pytorch", "PyTorch", "k8s", "Kubernetes"]
    result = deduplicate(raw)
    assert result.count("Python") == 1
    assert result.count("PyTorch") == 1
    assert result.count("Kubernetes") == 1
    assert len(result) == 3