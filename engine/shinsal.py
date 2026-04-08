# -*- coding: utf-8 -*-
"""
신살 1차: 도화(桃花), 역마(驛馬)
기준 지지군:
  - 寅午戌, 申子辰, 亥卯未, 巳酉丑
도화 위치:  寅午戌→卯 / 申子辰→酉 / 亥卯未→子 / 巳酉丑→午
역마 위치:  寅午戌→申 / 申子辰→寅 / 亥卯未→巳 / 巳酉丑→亥

판정: '기준 군'을 일지(또는 연지)에 두고, 네 기둥 중 해당 '도화/역마' 지지가 존재하면 신살 부여.
"""

from __future__ import annotations
from typing import Dict, List

GROUPS = {
    "寅午戌": set("寅午戌"),
    "申子辰": set("申子辰"),
    "亥卯未": set("亥卯未"),
    "巳酉丑": set("巳酉丑"),
}

PEACH = {  # 도화
    "寅午戌": "卯",
    "申子辰": "酉",
    "亥卯未": "子",
    "巳酉丑": "午",
}

TRAVEL = {  # 역마
    "寅午戌": "申",
    "申子辰": "寅",
    "亥卯未": "巳",
    "巳酉丑": "亥",
}

def _which_group(branch: str) -> str:
    for name, gr in GROUPS.items():
        if branch in gr:
            return name
    return ""

def detect_shinsal(pillars: Dict[str, Dict[str, str]]) -> Dict[str, List[str]]:
    """
    반환 예:
    {"year":["도화"], "month":[], "day":["역마"], "hour":[]}
    """
    result = {k: [] for k in ["year","month","day","hour"]}
    # 기준은 '일지'를 우선 사용
    day_branch = pillars.get("day", {}).get("branch", "")
    g = _which_group(day_branch)
    if not g:
        return result

    peach = PEACH[g]
    travel = TRAVEL[g]

    for key, pb in pillars.items():
        br = pb.get("branch", "")
        if br == peach:
            result[key].append("도화")
        if br == travel:
            result[key].append("역마")
    return result
