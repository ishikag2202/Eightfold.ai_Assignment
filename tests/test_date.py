import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.normalizers.date import normalize_yyyy_mm


def test_normalize_yyyy_mm():
    assert normalize_yyyy_mm("2021-03") == "2021-03"
    assert normalize_yyyy_mm("Mar 2021") == "2021-03"
    assert normalize_yyyy_mm("March 2021") == "2021-03"
    assert normalize_yyyy_mm(None) is None
    assert normalize_yyyy_mm("") is None
    assert normalize_yyyy_mm("not a date") is None