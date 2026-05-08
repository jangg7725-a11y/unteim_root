# -*- coding: utf-8 -*-
import os
import sys

# 프로젝트 루트에서 실행할 때 import가 되도록 보정 (윈도우/맥 공통)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest

from engine.shinsal_detector import detect_shinsal, analyze_shinsal_with_enrichment


def _find(hits, name):
    return [h for h in hits if h["name"] == name]


def test_detect_shinsal_return_shape():
    """detect_shinsal은 {items, summary}를 반환한다."""
    pillars = {
        "year": ("丙", "午"),
        "month": ("庚", "子"),
        "day": ("甲", "申"),
        "hour": ("癸", "卯"),
    }
    r = detect_shinsal(pillars, include_optional_goegang=True, include_ext_rules=True)
    assert isinstance(r, dict)
    assert "items" in r and "summary" in r
    assert isinstance(r["items"], list)
    assert isinstance(r["summary"], dict)
    assert len(r["items"]) >= 1


def test_twelve_lifestage_always_present():
    """연월일시 각 기둥에 대해 12운성 항목이 잡힌다."""
    pillars = {
        "year": ("丙", "午"),
        "month": ("庚", "子"),
        "day": ("甲", "申"),
        "hour": ("癸", "卯"),
    }
    hits = detect_shinsal(pillars, include_optional_goegang=True, include_ext_rules=True)["items"]
    twelve = [h for h in hits if "12운성" in h["name"]]
    assert len(twelve) >= 4


def test_cheoneul_guiin_甲_year_丑():
    """일간 甲 → 천을귀인 지지에 丑이 있으면 연지 적발."""
    pillars = {
        "year": ("丙", "丑"),
        "month": ("庚", "子"),
        "day": ("甲", "申"),
        "hour": ("癸", "卯"),
    }
    hits = detect_shinsal(pillars, include_optional_goegang=True, include_ext_rules=True)["items"]
    t = _find(hits, "천을귀인")
    assert t, f"천을귀인 미적발: {hits}"
    assert any(h["where"] == "year" and h["branch"] == "丑" for h in t)


def test_taohua_子日_卯지():
    """일지 子 → 도화 卯. 월지에 卯 배치 시 도화 적발."""
    pillars = {
        "year": ("丙", "午"),
        "month": ("庚", "卯"),
        "day": ("甲", "子"),
        "hour": ("癸", "酉"),
    }
    hits = detect_shinsal(pillars, include_optional_goegang=True, include_ext_rules=True)["items"]
    d = _find(hits, "도화")
    assert d, f"도화 미적발: {hits}"
    assert any(h["where"] == "month" and h["branch"] == "卯" for h in d)


def test_teneul_geng_day_uses_standard_table():
    """일간 庚은 천을귀인 지지 卯/巳를 사용한다."""
    pillars = {
        "year": ("丙", "卯"),
        "month": ("丁", "巳"),
        "day": ("庚", "子"),
        "hour": ("癸", "酉"),
    }
    hits = detect_shinsal(pillars, include_optional_goegang=True, include_ext_rules=True)["items"]
    t = _find(hits, "천을귀인")
    assert t, f"천을귀인 미적발: {hits}"
    assert any(h["where"] == "year" and h["branch"] == "卯" for h in t)
    assert any(h["where"] == "month" and h["branch"] == "巳" for h in t)


def test_analyze_shinsal_with_enrichment_loads_meta():
    """확장 메타 파일 로딩 후 설명 문자열이 채워진다."""
    pillars = {
        "year": ("丙", "卯"),
        "month": ("丁", "巳"),
        "day": ("庚", "子"),
        "hour": ("癸", "酉"),
    }
    out = analyze_shinsal_with_enrichment(pillars)
    assert "enriched" in out and "report" in out
    flat = out["enriched"].get("flat_list", [])
    assert isinstance(flat, list)
    if flat:
        assert "description" in flat[0]
