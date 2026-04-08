from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.sajuCalculator import calculate_saju


CASES_PATH = Path(__file__).with_name("saju_test_cases.json")
CASES = json.loads(CASES_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CASES, ids=[c["birth"] for c in CASES])
def test_calculate_saju_basic_pillars(case: dict) -> None:
    birth = case["birth"]
    p = calculate_saju(birth).as_dict()

    actual_year = f"{p['year']['gan']}{p['year']['ji']}"
    actual_month = f"{p['month']['gan']}{p['month']['ji']}"
    actual_day = f"{p['day']['gan']}{p['day']['ji']}"
    actual_hour = f"{p['hour']['gan']}{p['hour']['ji']}"

    assert actual_year == case["expected_year"]
    assert actual_month == case["expected_month"]
    assert actual_day == case["expected_day"]
    assert actual_hour == case["expected_hour"]
