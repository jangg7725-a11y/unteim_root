# -*- coding: utf-8 -*-
"""
unteim/engine/shinsal_score.py
- detect_shinsal() 결과(items: List[dict])를 받아 길/흉/주의 요약을 만든다.
- 학파/운영정책에 따라 GOOD/BAD/CAUTION 분류표만 바꾸면 된다.
"""

from __future__ import annotations
from typing import Any, Dict, List, Tuple

def verdict_label(verdict: str) -> str:
    # verdict()가 "길"/"흉"/"보통(중재)" 같은 문자열을 반환한다고 가정
    if verdict in ("길", "대길"):
        return "좋은 흐름(밀기)"
    if verdict in ("흉", "대흉"):
        return "주의 흐름(잠그기)"
    return "보통(혼재)"

# ✅ 기본 분류표 (운영하면서 조정하면 됨)
GOOD_NAMES = {
    "천을귀인", "천덕귀인", "월덕귀인", "문창귀인", "태극귀인", "복성귀인",
    "12운성:장생", "12운성:관대", "12운성:임관", "12운성:제왕",
}
CAUTION_NAMES = {
    "도화", "역마살", "괴강살", "양인살", "화개살",
}
BAD_NAMES = {
    "겁살", "재살", "망신살", "월살", "지살", "천살", "수옥살", "백호살",
}

# ✅ 점수 보정(정책)
# - 엔진에서 들어오는 weight를 기본으로 쓰고,
# - 길/흉/주의 성격에 따라 부호/감쇠를 준다.
POLARITY = {
    "good": +1,
    "caution": -1,  # 주의는 마이너스(약하게)
    "bad": -2,      # 흉은 더 강하게 마이너스
}

# ✅ 판정 기준(정책)
# total_score가:
#  +3 이상 : 길
#  -2 ~ +2 : 보통(혼재)
#  -3 이하 : 주의/흉
def _verdict(total_score: int) -> str:
    if total_score >= 3:
        return "길"
    if total_score <= -3:
        return "흉"
    return "보통(혼재)"


def _classify_name(name: str) -> str:
    # "12운성:제왕"처럼 접두가 붙는 것 대응
    if name in GOOD_NAMES:
        return "good"
    if name in BAD_NAMES:
        return "bad"
    if name in CAUTION_NAMES:
        return "caution"

    # 12운성은 기본적으로 중립/혼재로 두되, 위 GOOD_NAMES에 포함된 것만 길로 처리
    if name.startswith("12운성:"):
        return "neutral"

    return "neutral"


def summarize_shinsal(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    items: detect_shinsal()가 반환하는 list[dict]
      각 dict 예: {"name","where","branch","detail","weight"}

    반환:
      {
        "counts": {"good":x,"caution":y,"bad":z,"neutral":n,"total":t},
        "score": {"total": int, "good": int, "caution": int, "bad": int},
        "by_where": {"year": {...}, "month": {...}, ...},
        "verdict": "길|보통(혼재)|흉",
        "top_factors": [ ... 영향 큰 순 ... ]
      }
    """
    # 안전 정규화
    norm: List[Dict[str, Any]] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        name = str(it.get("name", ""))
        where = str(it.get("where", ""))
        branch = str(it.get("branch", ""))
        detail = str(it.get("detail", ""))
        w = it.get("weight", 1)
        try:
            weight = int(w)
        except Exception:
            weight = 1
        cls = _classify_name(name)

        # polarity 적용 점수
        if cls == "good":
            signed = weight * POLARITY["good"]
        elif cls == "bad":
            signed = weight * POLARITY["bad"]
        elif cls == "caution":
            signed = weight * POLARITY["caution"]
        else:
            signed = 0

        norm.append({
            "name": name, "where": where, "branch": branch, "detail": detail,
            "weight": weight, "class": cls, "signed_score": signed
        })

    # 집계
    counts = {"good": 0, "caution": 0, "bad": 0, "neutral": 0, "total": 0}
    score = {"total": 0, "good": 0, "caution": 0, "bad": 0}

    by_where: Dict[str, Dict[str, int]] = {
        "year": {"good": 0, "caution": 0, "bad": 0, "neutral": 0, "score": 0},
        "month": {"good": 0, "caution": 0, "bad": 0, "neutral": 0, "score": 0},
        "day": {"good": 0, "caution": 0, "bad": 0, "neutral": 0, "score": 0},
        "hour": {"good": 0, "caution": 0, "bad": 0, "neutral": 0, "score": 0},
    }

    for it in norm:
        cls = it["class"]
        signed = it["signed_score"]
        where = it["where"] if it["where"] in by_where else "day"

        counts[cls] += 1
        counts["total"] += 1

        if cls in ("good", "bad", "caution"):
            score[cls] += signed
            score["total"] += signed
            by_where[where][cls] += 1
            by_where[where]["score"] += signed
        else:
            by_where[where]["neutral"] += 1

    # 영향 큰 순(절댓값 기준)
    top_factors = sorted(
        norm,
        key=lambda x: abs(int(x.get("signed_score", 0))),
        reverse=True
    )[:8]

    v = _verdict(score["total"])

    return {
        "counts": counts,
        "score": score,
        "by_where": by_where,
        "verdict": v,
        "verdict_label": verdict_label(v),  # ✅ 이 줄이 핵심 (없으면 None/미출력)
        "top_factors": top_factors,
   }

