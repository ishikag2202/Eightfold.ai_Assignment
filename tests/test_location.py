import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.normalizers.location import normalize_location


def test_full_location_string():
    result = normalize_location("San Francisco, CA, USA")
    assert result == {"city": "San Francisco", "region": "CA", "country": "US"}


def test_city_and_state_only_infers_us():
    result = normalize_location("Austin, TX")
    assert result["country"] == "US"


def test_empty_or_none():
    assert normalize_location(None) is None
    assert normalize_location("") is None


def test_city_only():
    result = normalize_location("Berlin")
    assert result["city"] == "Berlin"
    assert result["region"] is None