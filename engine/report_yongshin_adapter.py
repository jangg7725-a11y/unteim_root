"""
report_yongshin_adapter.py
사주 전체 리포트에 용신/희신/기신 내용을 붙여주는 어댑터
"""

from __future__ import annotations
from typing import Dict, Any

from .yongshin_analyzer import analyze_yongshin_context


def enrich_report_with_yongshin(pillars: Dict[str, Any], base_report: Dict[str, Any]) -> Dict[str, Any]:
    """
    pillars: 사주 전체 계산 결과 (오행강약, 십신, 격국, 용신, 희신, 기신 포함)
    base_report: 기존 리포트 (오행/12운성/신살 등)

    리턴: base_report에 용신/희신/기신 해석이 추가된 형태
    """

    pillar_block = pillars.get("pillars")
    if not isinstance(pillar_block, dict):
        pillar_block = pillars if isinstance(pillars.get("year"), dict) else {}

    oheng = pillars.get("oheng") or pillars.get("oheng_strength")
    if not isinstance(oheng, dict):
        oheng = {}

    geukguk = pillars.get("geukguk")
    if not isinstance(geukguk, dict) and isinstance(pillars.get("analysis"), dict):
        geukguk = (
            (pillars["analysis"].get("base_structure") or {}).get("geukguk")
            or pillars["analysis"].get("geukguk")
        )
    if not isinstance(geukguk, dict):
        geukguk = {}

    context = {
        "pillars": pillar_block,
        "oheng": oheng,
        "oheng_strength": pillars.get("oheng_strength"),
        "geukguk": geukguk,
        "day_master": pillars.get("day_master"),
        "yongshin": pillars.get("yongshin_info"),
        "pattern_type": pillars.get("pattern_type"),
        "useful_gods_reason": pillars.get("useful_gods_reason"),
    }

    ys_dict = analyze_yongshin_context(context)

    base_report["yongshin_section"] = {
        "용신해석": ys_dict["yongshin_text"],
        "희신해석": ys_dict["huishin_text"],
        "기신해석": ys_dict["gishin_text"],
        "실전가이드": ys_dict["advice_text"],
    }

    return base_report
