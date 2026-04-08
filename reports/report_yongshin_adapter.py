# unteim/reports/report_yongshin_adapter.py
# -*- coding: utf-8 -*-

"""
호환 브릿지(파일명 불일치 해결):
- main_report.py 는 report_yongshin_adapter 를 import 함
- 실제 구현은 report_yongshin_luck_adapter.py 에 있음
"""

from __future__ import annotations

try:
    # 실제 파일(현재 프로젝트에 존재)
    from .report_yongshin_luck_adapter import enrich_report_with_yongshin  # type: ignore
except Exception:
    # 없거나 함수명이 다를 때, 메인 리포트가 안 깨지도록 no-op 처리
    def enrich_report_with_yongshin(report: dict) -> dict:  # type: ignore
        return report
