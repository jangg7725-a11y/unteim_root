# -*- coding: utf-8 -*-
"""
천간/지지 → 오행 매핑
"""

from __future__ import annotations
from typing import Dict

# 천간 오행
STEM_OHENG: Dict[str, str] = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

# 지지 오행
BRANCH_OHENG: Dict[str, str] = {
    "子": "水",
    "丑": "土",
    "寅": "木",
    "卯": "木",
    "辰": "土",
    "巳": "火",
    "午": "火",
    "未": "土",
    "申": "金",
    "酉": "金",
    "戌": "土",
    "亥": "水",
}

def map_pillars_oheng(pillars: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    """
    pillars = {
      "year": {"stem": "丙", "branch": "午"},
      "month": {"stem": "...", "branch": "..."},
      "day": {"stem": "...", "branch": "..."},
      "hour": {"stem": "...", "branch": "..."},
    }
    반환: 각 기둥에 stem_element / branch_element 추가한 딕셔너리
    """
    out: Dict[str, Dict[str, str]] = {}
    for key, pb in pillars.items():
        s = pb.get("stem", "")
        b = pb.get("branch", "")
        out[key] = {
            "stem": s,
            "branch": b,
            "stem_element": STEM_OHENG.get(s, ""),
            "branch_element": BRANCH_OHENG.get(b, ""),
        }
    return out
