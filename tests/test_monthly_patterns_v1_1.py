# unteim/tests/test_monthly_patterns_v1_1.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from engine.monthly_patterns_v1_1 import detect_month_patterns_v1_1


def test_detect_month_patterns_v1_1_never_crash():
    report = {"analysis": {}, "extra": {}, "pillars": {"month": {"ji": "子"}}}
    out = detect_month_patterns_v1_1(report)
    assert isinstance(out, list)
    assert len(out) >= 1
    assert "tone" in out[0]
