# -*- coding: utf-8 -*-
"""
engine.wolwoonCalculator
- 월운(연월운) 리스트를 생성하는 간단 엔진 초안.

⚠️ 1차 버전: 1984-01(갑자월)을 기준으로 60갑자 월운을 순환 계산하는 방식입니다.
   - 향후 절입일/절기 기반 정밀 월운 계산은 추후 KASI / solar_terms 연동 후 교체 예정입니다.
"""

from __future__ import annotations

from typing import List, Dict, Any

# 10간 / 12지
HEAVENLY_STEMS = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
EARTHLY_BRANCHES = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]


def _month_ganji_from_index(idx: int) -> str:
    """
    0 기반 인덱스(idx)에서 월간 간지 문자열을 만든다.
    - idx: 0,1,2,... 에 대해 60갑자를 순환.
    """
    stem = HEAVENLY_STEMS[idx % 10]
    branch = EARTHLY_BRANCHES[idx % 12]
    return stem + branch


def calculate_wolwoon(
    start_year: int,
    start_month: int = 1,
    num_months: int = 12,
) -> List[Dict[str, Any]]:
    """
    월운 리스트 생성 엔진 (1차 버전).

    Parameters
    ----------
    start_year : int
        시작 기준 연도 (양력 연도).
    start_month : int, default 1
        시작 기준 월 (1~12).
    num_months : int, default 12
        생성할 월운 개수 (개월 수).

    Returns
    -------
    List[Dict[str, Any]]
        각 월에 대한 정보가 담긴 리스트.
        예:
        [
            {"year": 2025, "month": 1, "ganji": "갑자"},
            {"year": 2025, "month": 2, "ganji": "을축"},
            ...
        ]

    Notes
    -----
    - 기준점: 1984년 1월을 갑자월(0번 인덱스)로 두고,
      (연도, 월)을 0 기반 오프셋으로 바꾼 뒤 60갑자를 순환합니다.
    - 향후 절입일 기반 정밀 월운은 solar_terms 모듈을 이용해 교체 예정입니다.
    """
    results: List[Dict[str, Any]] = []

    # 기준 연/월: 1984-01을 offset 0으로 둔다.
    base_year = 1984
    base_month = 1

    # 시작점 offset 계산
    # 예: 1984-01 -> 0, 1984-02 -> 1, ... , 1985-01 -> 12 ...
    start_offset = (start_year - base_year) * 12 + (start_month - base_month)

    for i in range(num_months):
        offset = start_offset + i

        # 해당 offset에 대응되는 연/월 계산
        year = base_year + (base_month - 1 + offset) // 12
        month = (base_month - 1 + offset) % 12 + 1

        ganji = _month_ganji_from_index(offset)

        results.append(
            {
                "year": year,
                "month": month,
                "ganji": ganji,
            }
        )

    return results


if __name__ == "__main__":
    # 간단 테스트
    sample = calculate_wolwoon(start_year=2025, start_month=1, num_months=12)
    from pprint import pprint

    pprint(sample)
