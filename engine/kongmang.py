# unteim/engine/kongwang.py
# -*- coding: utf-8 -*-
"""
공망(旬空) 계산
- 일주(일간+일지) index(0~59, 0=甲子)로 10간(旬)을 구해 빈 지지 2개를 산출.
- 甲子旬: 戌亥 / 甲戌旬: 申酉 / 甲申旬: 午未 / 甲午旬: 辰巳 / 甲辰旬: 寅卯 / 甲寅旬: 子丑
"""

from __future__ import annotations
from typing import Dict, List, Tuple
from datetime import datetime
from zoneinfo import ZoneInfo

from .pillars import d_ganzhi_from_solar, BRANCHES, STEMS

KST = ZoneInfo("Asia/Seoul")

# 10일씩 6개 '旬'에 대응하는 공망 테이블(순서대로 0..5)
_XUN_VOID: List[Tuple[str, str]] = [
    ("戌", "亥"),  # 0: 甲子旬 (0~9)
    ("申", "酉"),  # 1: 甲戌旬 (10~19)
    ("午", "未"),  # 2: 甲申旬 (20~29)
    ("辰", "巳"),  # 3: 甲午旬 (30~39)
    ("寅", "卯"),  # 4: 甲辰旬 (40~49)
    ("子", "丑"),  # 5: 甲寅旬 (50~59)
]

def _day_index_0_based(dt_kst: datetime) -> int:
    """1984-02-02 甲子 = 0 기준 일간지 index"""
    from .pillars import jdn_from_datetime_kst
    base = datetime(1984, 2, 2, 0, 0, tzinfo=KST)
    j0 = jdn_from_datetime_kst(base)
    j1 = jdn_from_datetime_kst(dt_kst)
    return (j1 - j0) % 60

def kongmang_info(dt_kst: datetime, pillars: Dict[str, Dict[str, str]]) -> Dict[str, object]:
    """
    반환:
    {
      "void_pair": ["戌","亥"],
      "flags": {"year": false, "month": true, "day": false, "hour": false}
    }
    """
    if dt_kst.tzinfo is None:
        dt_kst = dt_kst.replace(tzinfo=KST)
    day_idx = _day_index_0_based(dt_kst)
    xun = day_idx // 10
    v1, v2 = _XUN_VOID[xun]

    flags = {}
    for key, pb in pillars.items():
        br = pb.get("branch", "")
        flags[key] = (br == v1 or br == v2)

    return {"void_pair": [v1, v2], "flags": flags}

