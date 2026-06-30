import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.normalizers.years import calculate_years_experience


def test_calculate_with_end_dates():
    exp = [
        {"start": "2018-06", "end": "2021-02"},  # ~2.67 years
        {"start": "2021-03", "end": "2023-03"},  # 2 years
    ]
    result = calculate_years_experience(exp)
    assert 4.5 < result < 4.8


def test_calculate_with_open_ended_job():
    exp = [{"start": "2021-03", "end": None}]
    result = calculate_years_experience(exp)
    assert result > 0  # depends on today's date, just confirm it computed something


def test_calculate_empty():
    assert calculate_years_experience([]) is None
    assert calculate_years_experience(None) is None


def test_calculate_unparseable_dates():
    exp = [{"start": None, "end": None}]
    assert calculate_years_experience(exp) is None