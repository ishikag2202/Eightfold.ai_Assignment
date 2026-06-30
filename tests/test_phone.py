import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.normalizers.phone import normalize_e164, get_region


def test_normalize_e164():
    assert normalize_e164("4155550192") == "+14155550192"
    assert normalize_e164("+1-415-555-0192") == "+14155550192"
    assert normalize_e164("415 555 0192") == "+14155550192"
    assert normalize_e164("garbage") is None
    assert normalize_e164(None) is None


def test_get_region():
    assert get_region("+14155550192") == "US"