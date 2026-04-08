# unteim/tests/test_monthly_patterns_v1.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from engine.monthly_patterns_v1 import detect_month_patterns_v1


def test_detect_month_patterns_v1_never_crash():
    # 최소 report 형태(데이터 없어도 절대 죽지 않아야 함)
    report = {"analysis": {}, "extra": {}}
    out = detect_month_patterns_v1(report)
    assert isinstance(out, list)
    assert len(out) >= 1
    assert "id" in out[0]
    assert "level" in out[0]
