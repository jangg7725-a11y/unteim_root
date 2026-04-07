# scripts/run_monthly_report.py
# -*- coding: utf-8 -*-
#
# python scripts/run_monthly_report.py 실행 시 sys.path[0]이 scripts/가 되어
# 형제 디렉터리인 engine/, reports/를 찾지 못함 → 루트를 path에 넣음.

import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from engine.sajuCalculator import calculate_saju
from engine.full_analyzer import analyze_full
from engine.types import SajuPillars

# ✅ Top3 만들기 위해 반드시 필요
from engine.monthly_patterns_v1_1 import attach_month_patterns_v1_1

# ✅ 최종 PDF 생성(월간 리포트)
from reports.monthly_report import build_monthly_report_pdf


def main() -> None:
    # =========================
    # 입력값
    # =========================
    name = "장경옥"
    sex = "여자"
    birth = "1990-01-01 09:30"

    # =========================
    # 1) 사주 계산 + 전체 분석
    # =========================
    saju: SajuPillars = calculate_saju(birth)
    # 선택형 주제(옵션): selected_topics=["직장운", "재물운", "건강운"] 등 → result["selected_reports"]
    report = analyze_full(saju.as_dict(), birth_str=birth)

    
    # =========================
    # 2) ✅ 이름/성별 연결 (Unknown 방지)
    # =========================
    report.setdefault("profile", {})
    report["profile"]["name"] = name
    report["profile"]["sex"] = sex

    # =========================
    # 3) ✅ 월간 패턴 부착 (Top3 생성 핵심)
    # =========================
    report = attach_month_patterns_v1_1(report)

    from datetime import datetime

    now = datetime.now()

    report.setdefault("meta", {})
    report["meta"].setdefault("year", now.year)
    report["meta"].setdefault("month", now.month)
    # =========================
    # 4) PDF 생성 (항상 같은 파일로 저장)
    # =========================
    out_path = Path("out/monthly_report.pdf")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    build_monthly_report_pdf(
        report=report,
        out_path=str(out_path),
    )

    print(f"[OK] monthly report generated -> {out_path}")


if __name__ == "__main__":
    main()
