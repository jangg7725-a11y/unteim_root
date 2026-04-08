# unteim/scripts/run_full_report.py
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from engine.sajuCalculator import calculate_saju
from engine.full_analyzer import analyze_full
from engine.types import SajuPillars


def main() -> None:
    # --------------------------------------------------------
    # 1) 입력값 (테스트용)
    #    - 형식: 'YYYY-MM-DD HH:MM' (KST)
    # --------------------------------------------------------
    birth_str: str = "1966-11-04 02:05"

    # 2) RAW 명식 계산 → SajuPillars (gan/ji 배열)
    saju: SajuPillars = calculate_saju(birth_str)

    # 3) pillars: year/month/day/hour → {gan, ji} (coerce_pillars 호환)
    pillars: Dict[str, Any] = saju.as_dict()

    # 4) 전체 분석 실행
    full: Dict[str, Any] = analyze_full(pillars, birth_str=birth_str)

    # full 안에 report 키가 있으면 그걸 사용
    report: Dict[str, Any] = full.get("report", full)

    # --------------------------------------------------------
    # 출력 1: 기본 명식
    # --------------------------------------------------------
    print("[명식] (엔진 계산 결과)")
    print("  년주:", pillars.get("year"))
    print("  월주:", pillars.get("month"))
    print("  일주:", pillars.get("day"))
    print("  시주:", pillars.get("hour"))
    print("-" * 60)
    # --------------------------------------------------------
    # 출력 1.5: 일간 신강/신약 판별
    # --------------------------------------------------------
    shinkang = report.get("shinkang") or {}
    print("\n[일간 신강/신약 판별]")
    status = shinkang.get("status") or "판별 정보 없음"
    print("  - 상태:", status)

    day_elem = shinkang.get("day_element")
    if isinstance(day_elem, str) and day_elem:
        print("  - 일간 오행:", day_elem)

    ratio = shinkang.get("ratio")
    if isinstance(ratio, (int, float)):
        print(f"  - 일간 비중: {ratio * 100:.1f}%")

    print("-" * 60)

    # --------------------------------------------------------
    # 출력 2: 용신·희신·기신 해석
    # --------------------------------------------------------
    ys = report.get("yongshin_raw", {})
    print("\n[용신·희신·기신 해석]")
    print("  - 용신해석:", ys.get("용신해석"))
    print("  - 희신해석:", ys.get("희신해석"))
    print("  - 기신해석:", ys.get("기신해석"))
    print("  - 실전가이드:\n")
    print(ys.get("실전가이드", "(정보 없음)"))
    print("-" * 60)

    # --------------------------------------------------------
    # 출력 3: 용신 호운/주의 시기
    # --------------------------------------------------------
    yl = report.get("yongshin_luck") or {}


    print("\n[용신 호운/주의 시기 요약]")
    print(yl.get("summary", "(요약 없음)"))

    # 연도 단위
    fav_years = yl.get("favorable_years", [])
    cau_years = yl.get("caution_years", [])

    print("\n  > 호운 연도:")
    if fav_years:
        for y in fav_years:
            print("    -", y.get("year"), "년 | 점수:", y.get("score"),
                  "| 오행:", y.get("elements"))
    else:
        print("    없음")

    print("\n  > 주의 연도:")
    if cau_years:
        for y in cau_years:
            print("    -", y.get("year"), "년 | 점수:", y.get("score"),
                  "| 오행:", y.get("elements"))
    else:
        print("    없음")

    # 월 단위
    monthly_highlights = yl.get("monthly_highlights", {})
    fav_months = monthly_highlights.get("favorable_months", [])
    cau_months = monthly_highlights.get("caution_months", [])

    print("\n  > 호운 월:")
    if fav_months:
        for m in fav_months[:10]:
            print("    -", m.get("year"), "년", m.get("month"), "월 | 점수:",
                  m.get("score"), "| 오행:", m.get("elements"))
    else:
        print("    없음")

    print("\n  > 주의 월:")
    if cau_months:
        for m in cau_months[:10]:
            print("    -", m.get("year"), "년", m.get("month"), "월 | 점수:",
                  m.get("score"), "| 오행:", m.get("elements"))
    else:
        print("    없음")

    print("\n[OK] 분석 완료")
    print("-" * 60)


if __name__ == "__main__":
    main()
