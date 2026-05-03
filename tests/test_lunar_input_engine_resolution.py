# -*- coding: utf-8 -*-
"""
음력 입력 → 양력(KST) 정규화 후 절기·대운 등 엔진이 동일한 birth_str을 쓰는지 검증.

- `engine.counsel_birth.normalize_birth_string`: korean-lunar-calendar 기준 음력→양력
- 사주/대운은 항상 변환된 양력 시각으로만 계산해야 함 (양력 입력이면 그대로)
"""

from __future__ import annotations

from engine.counsel_birth import normalize_birth_string
from engine.daewoon_engine import DaewoonEngine
from engine.sajuCalculator import calculate_saju


def test_lunar_1966_11_04_resolves_to_solar_december() -> None:
    """음력 병오년 11월 4일 → 양력 날짜(한국 음력 라이브러리 기준)."""
    solar = normalize_birth_string("1966-11-04", "02:05", "lunar")
    assert solar == "1966-12-15 02:05"


def test_daewoon_differs_lunar_vs_mistaken_solar_same_numbers() -> None:
    """
    동일 숫자(1966-11-04 02:05)를 음력 vs 양력으로 두면 대운 시작나이가 달라져야 함.
    (과거에 양력으로 착각하고 검증하면 만세력과 불일치가 난다.)
    """
    resolved = normalize_birth_string("1966-11-04", "02:05", "lunar")
    mistaken_solar = "1966-11-04 02:05"

    eng = DaewoonEngine()
    d_ok = eng.run(birth_str=resolved, gender="M", count=1)
    d_wrong = eng.run(birth_str=mistaken_solar, gender="M", count=1)

    assert d_ok[0]["start_age"] != d_wrong[0]["start_age"]
    # 음력→양력(12/15) 기준 남성 순행 첫 대운 시작나이(반올림)는 7 근방
    assert d_ok[0]["start_age"] == 7
    assert d_wrong[0]["start_age"] == 1


def test_lunar_1972_07_24_18_00_pillars_regression() -> None:
    """
    사용자 제보 회귀:
    음력 1972-07-24 18:00(평달) → 양력 1972-09-01 18:00 기준
    사주 원국은 壬子 / 戊申 / 乙未 / 乙酉 이어야 한다.
    """
    solar = normalize_birth_string("1972-07-24", "18:00", "lunar")
    assert solar == "1972-09-01 18:00"

    p = calculate_saju(solar).as_dict()
    assert f"{p['year']['gan']}{p['year']['ji']}" == "壬子"
    assert f"{p['month']['gan']}{p['month']['ji']}" == "戊申"
    assert f"{p['day']['gan']}{p['day']['ji']}" == "乙未"
    assert f"{p['hour']['gan']}{p['hour']['ji']}" == "乙酉"
