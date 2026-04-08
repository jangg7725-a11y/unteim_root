# -*- coding: utf-8 -*-
"""
12운성 계산 (일간 기준, 지지 대상)
- 규칙:
  1) 시작점(長生 지지)은 일간(천간)에 따라 정해진다.
  2) 일간이 陽(甲丙戊庚壬)이면 12단계를 '순행'
     일간이 陰(乙丁己辛癸)이면 12단계를 '역행'
  3) 각 기둥의 'branch'에 해당하는 운성을 부여한다.

참고: 장생 시작지지 표 (관용)
甲→亥, 乙→午, 丙→寅, 丁→酉, 戊→寅, 己→酉, 庚→巳, 辛→子, 壬→申, 癸→卯
"""

from __future__ import annotations
from typing import Dict, List

BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]

# 12운성 라벨
FORTUNES = ["長生","沐浴","冠帶","臨官","帝旺","衰","病","死","墓","絕","胎","養"]

# 일간 → 長生 시작 지지 (index)
CHANGSHENG_START = {
    "甲": "亥", "乙": "午",
    "丙": "寅", "丁": "酉",
    "戊": "寅", "己": "酉",
    "庚": "巳", "辛": "子",
    "壬": "申", "癸": "卯",
}
YANG_STEMS = set("甲丙戊庚壬")
YIN_STEMS  = set("乙丁己辛癸")

def _fortune_map_for_day_stem(day_stem: str) -> Dict[str, str]:
    """일간에 대한 지지→운성 매핑 테이블 생성"""
    start_branch = CHANGSHENG_START[day_stem]
    start_idx = BRANCHES.index(start_branch)

    # 진행 방향: 양간=순행, 음간=역행
    forward = (day_stem in YANG_STEMS)

    mapping: Dict[str, str] = {}
    for i, fortune in enumerate(FORTUNES):
        # i=0이 長生
        offset = i if forward else -i
        idx = (start_idx + offset) % 12
        mapping[BRANCHES[idx]] = fortune
    return mapping

def map_twelve_fortunes(pillars: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    """
    입력 pillars 예:
      {"year":{"stem":"丙","branch":"午"}, "month":..., "day":..., "hour":...}
    반환:
      {"year":{"branch":"午","fortune":"帝旺"}, ...}
    (운성은 '일간' 기준으로 각 기둥의 branch에 부여)
    """
    day_stem = pillars.get("day", {}).get("stem", "")
    if not day_stem:
        return {}

    table = _fortune_map_for_day_stem(day_stem)

    out: Dict[str, Dict[str, str]] = {}
    for key, pb in pillars.items():
        br = pb.get("branch", "")
        out[key] = {
            "branch": br,
            "fortune": table.get(br, "")
        }
    return out
