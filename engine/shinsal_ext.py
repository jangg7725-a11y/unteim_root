# -*- coding: utf-8 -*-
"""
shinsal_ext.py
- 신살 확장팩(홍염, 문창, 천을귀인, 괴강 등)을 규칙 테이블로 계산.
- 규칙은 JSON 파일(unteim/data/shinsal_ext_rules.json)로 외부 관리.
- JSON이 없으면 내장 예시 규칙(아주 보수적 최소셋)으로 동작.

입력:
    pillars = {
        "year": {"stem": "丙", "branch": "午"},
        "month": {"stem": "辛", "branch": "亥"},
        "day": {"stem": "丁", "branch": "巳"},
        "hour": {"stem": "辛", "branch": "丑"},
    }

출력:
    {"year": [...], "month":[...], "day":[...], "hour":[...]}

규칙 JSON 스키마(배열):
[
  {
    "name": "문창",
    "by": "day_branch",              # 기준: year_branch | month_branch | day_branch | hour_branch | day_stem ...
    "match": ["子","午"],             # 기준값이 이 목록 중 하나일 때
    "place": "year",                  # 표기 위치: year|month|day|hour|all
    "label": "문창",                  # 출력 라벨 (생략 시 name 사용)
    "note": "설명(선택)"
  },
  {
    "name": "천을귀인",
    "by": "day_stem",
    "map": {                          # 기준값별 매핑(학교별 차이 큰 룰에 적합)
      "甲":"丑未", "乙":"子申", "丙":"亥酉", "丁":"亥酉",
      "戊":"丑未", "己":"子申", "庚":"丑未", "辛":"亥酉",
      "壬":"寅午", "癸":"卯巳"
    },
    "contains": "branch",             # day/month/year/hour 중 branch 에 해당하면 적발
    "place": "all",
    "label": "천을귀인"
  }
]
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Any

# 규칙 파일 경로
RULE_PATH = Path(__file__).resolve().parent.parent / "data" / "shinsal_ext_rules.json"

# 한자 세트(간·지)
STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"

def _safe(s: str) -> str:
    return s.strip()

def _load_rules() -> List[Dict[str, Any]]:
    if RULE_PATH.exists():
        with open(RULE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    # ▷ 기본(아주 최소) 내장 예시룰: 학파 차 큰 룰들은 템플릿만 제공
    # - 홍염(紅艶): (예시) 일지 기준 寅午戌 → 午에 홍염 등 다양한 학파가 있어 템플릿용
    # - 문창(文昌): (예시) 일지 子午 에 문창 카드 부여 (샘플)
    # - 천을귀인: 가장 흔한 표준 테이블을 map으로 제공(가지런)
    # - 괴강: 일간이 庚일 때 辰戌丑未 등(학파 편차 큼 → 템플릿)
    return [
        # 문창(샘플)
        {"name": "문창", "by": "day_branch", "match": ["子", "午"], "place": "all", "label": "문창"},
        # 천을귀인(흔히 쓰는 맵핑): 일간 기준
        {
            "name": "천을귀인",
            "by": "day_stem",
            "map": {
                "甲": "丑未", "乙": "子申", "丙": "亥酉", "丁": "亥酉",
                "戊": "丑未", "己": "子申", "庚": "丑未", "辛": "亥酉",
                "壬": "寅午", "癸": "卯巳"
            },
            "contains": "branch",
            "place": "all",
            "label": "천을귀인"
        },
        # 괴강(샘플): 학파 차이가 큽니다 — 템플릿
        {"name": "괴강", "by": "day_stem", "match": ["庚"], "place": "day", "label": "괴강"},
        # 홍염(샘플)
        {"name": "홍염", "by": "day_branch", "match": ["午"], "place": "all", "label": "紅艶"},
    ]

def _get_value(pillars: Dict[str, Dict[str, str]], key: str) -> str:
    if key == "year_stem":   return pillars["year"]["stem"]
    if key == "year_branch": return pillars["year"]["branch"]
    if key == "month_stem":  return pillars["month"]["stem"]
    if key == "month_branch":return pillars["month"]["branch"]
    if key == "day_stem":    return pillars["day"]["stem"]
    if key == "day_branch":  return pillars["day"]["branch"]
    if key == "hour_stem":   return pillars["hour"]["stem"]
    if key == "hour_branch": return pillars["hour"]["branch"]
    raise KeyError(key)

def _places() -> Dict[str, List[str]]:
    return {
        "year":  ["year"],
        "month": ["month"],
        "day":   ["day"],
        "hour":  ["hour"],
        "all":   ["year", "month", "day", "hour"],
    }

def detect_shinsal_ext(pillars: Dict[str, Dict[str, str]]) -> Dict[str, List[str]]:
    """
    확장 신살 결과 반환.
    """
    rules = _load_rules()
    out = {"year": [], "month": [], "day": [], "hour": []}
    place_map = _places()

    # 모든 지지(4지) 묶음 — contains 검사 때 사용
    four_branches = {
        "year":  pillars["year"]["branch"],
        "month": pillars["month"]["branch"],
        "day":   pillars["day"]["branch"],
        "hour":  pillars["hour"]["branch"],
    }
    four_stems = {
        "year":  pillars["year"]["stem"],
        "month": pillars["month"]["stem"],
        "day":   pillars["day"]["stem"],
        "hour":  pillars["hour"]["stem"],
    }

    for r in rules:
        name = r.get("label") or r.get("name") or "신살"
        by   = r.get("by", "")
        plc  = r.get("place", "all")
        targets = place_map.get(plc, place_map["all"])

        # 1) 단순 match 목록: 기준값이 match에 들어가면 적발
        if "match" in r and by:
            src = _get_value(pillars, by)
            if src in r["match"]:
                for p in targets:
                    out[p].append(name)
            continue

        # 2) map + contains: 기준 키(by)값으로 map에서 허용지지/간을 얻고,
        #    4기둥에 그 값이 포함되면 해당 위치 기록
        if "map" in r and by:
            src = _get_value(pillars, by)
            allow = _safe(r["map"].get(src, "")) if isinstance(r["map"], dict) else ""
            if not allow:
                continue
            # 허용문자 집합 (예: "丑未" → {"丑","未"})
            allow_set = set(allow)

            contains_field = r.get("contains", "branch")  # branch|stem
            pool = four_branches if contains_field == "branch" else four_stems

            for p in targets:
                if pool[p] in allow_set:
                    out[p].append(name)

    # 중복 제거(표시 예쁘게)
    for k in out:
        if out[k]:
            seen = set()
            uniq = []
            for v in out[k]:
                if v not in seen:
                    seen.add(v)
                    uniq.append(v)
            out[k] = uniq
    return out
def detect_shinsal_extended(*args, **kwargs):
    return detect_shinsal_ext(*args, **kwargs)
