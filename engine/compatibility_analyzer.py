# -*- coding: utf-8 -*-
"""사주 기반 궁합 분석 엔진 (MVP).

입력: 두 사람 birth_str("YYYY-MM-DD HH:MM"), gender
출력: 점수/요약/관계 가이드 JSON
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from engine.full_analyzer import analyze_full
from engine.sajuCalculator import calculate_saju

STEM_TO_ELEMENT: Dict[str, str] = {
    "甲": "wood",
    "乙": "wood",
    "丙": "fire",
    "丁": "fire",
    "戊": "earth",
    "己": "earth",
    "庚": "metal",
    "辛": "metal",
    "壬": "water",
    "癸": "water",
}

STEM_TO_YINYANG: Dict[str, str] = {
    "甲": "yang",
    "乙": "yin",
    "丙": "yang",
    "丁": "yin",
    "戊": "yang",
    "己": "yin",
    "庚": "yang",
    "辛": "yin",
    "壬": "yang",
    "癸": "yin",
}

GEN_MAP = {"wood": "fire", "fire": "earth", "earth": "metal", "metal": "water", "water": "wood"}
CTRL_MAP = {"wood": "earth", "earth": "water", "water": "fire", "fire": "metal", "metal": "wood"}

BRANCH_COMBINE = {"子丑", "寅亥", "卯戌", "辰酉", "巳申", "午未"}
BRANCH_CLASH = {"子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥"}
BRANCH_HARM = {"子未", "丑午", "寅巳", "卯辰", "申亥", "酉戌"}
BRANCH_PUNISH = {"寅巳", "巳申", "申寅", "丑戌", "戌未", "未丑", "子卯"}


def _stem_relation(a: str, b: str) -> str:
    if a == b:
        return "same"
    ea = STEM_TO_ELEMENT.get(a)
    eb = STEM_TO_ELEMENT.get(b)
    if not ea or not eb:
        return "neutral"
    if GEN_MAP[ea] == eb or GEN_MAP[eb] == ea:
        return "generate"
    if CTRL_MAP[ea] == eb or CTRL_MAP[eb] == ea:
        return "control"
    return "neutral"


def _ten_god_label(day_stem_self: str, day_stem_other: str) -> str:
    """상대 일간이 나에게 어떤 십신 성향인지 간략 라벨."""
    e_self = STEM_TO_ELEMENT.get(day_stem_self)
    e_other = STEM_TO_ELEMENT.get(day_stem_other)
    y_self = STEM_TO_YINYANG.get(day_stem_self)
    y_other = STEM_TO_YINYANG.get(day_stem_other)
    if not e_self or not e_other or not y_self or not y_other:
        return "비견/겁재"
    same_yin_yang = y_self == y_other
    if e_self == e_other:
        return "비견" if same_yin_yang else "겁재"
    if GEN_MAP[e_other] == e_self:
        return "정인" if same_yin_yang else "편인"
    if GEN_MAP[e_self] == e_other:
        return "식신" if same_yin_yang else "상관"
    if CTRL_MAP[e_self] == e_other:
        return "정재" if same_yin_yang else "편재"
    if CTRL_MAP[e_other] == e_self:
        return "정관" if same_yin_yang else "편관"
    return "비견/겁재"


def _pair_set(a: str, b: str) -> str:
    return "".join(sorted([a, b]))


def _collect_branch_relations(b1: Iterable[str], b2: Iterable[str]) -> Dict[str, int]:
    out = {"combine": 0, "clash": 0, "harm": 0, "punish": 0}
    for x in b1:
        for y in b2:
            p = _pair_set(x, y)
            if p in BRANCH_COMBINE:
                out["combine"] += 1
            if p in BRANCH_CLASH:
                out["clash"] += 1
            if p in BRANCH_HARM:
                out["harm"] += 1
            if p in BRANCH_PUNISH:
                out["punish"] += 1
    return out


def _score_to_star(score_100: float) -> int:
    if score_100 >= 85:
        return 5
    if score_100 >= 70:
        return 4
    if score_100 >= 55:
        return 3
    if score_100 >= 40:
        return 2
    return 1


def _safe_report(pillars: Any, birth: str) -> Dict[str, Any]:
    try:
        r = analyze_full(pillars, birth_str=birth)
        return r if isinstance(r, dict) else {}
    except Exception:
        return {}


def _extract_yongshin_elements(report: Dict[str, Any]) -> List[str]:
    analysis_obj = report.get("analysis")
    a: Dict[str, Any] = analysis_obj if isinstance(analysis_obj, dict) else {}
    yongshin_obj = a.get("yongshin")
    ys: Dict[str, Any] = yongshin_obj if isinstance(yongshin_obj, dict) else {}
    vals = []
    for k in ("yongshin", "heeshin", "gishin", "axis"):
        v = ys.get(k)
        if isinstance(v, str):
            vals.append(v.lower())
        elif isinstance(v, list):
            vals.extend(str(x).lower() for x in v)
    return vals


def analyze_compatibility(
    *,
    birth1: str,
    gender1: str,
    birth2: str,
    gender2: str,
) -> Dict[str, Any]:
    p1 = calculate_saju(birth1)
    p2 = calculate_saju(birth2)
    r1 = _safe_report(p1, birth1)
    r2 = _safe_report(p2, birth2)

    d1 = str(p1.gan[2])
    d2 = str(p2.gan[2])
    rel = _stem_relation(d1, d2)

    e1 = [STEM_TO_ELEMENT.get(str(g), "unknown") for g in p1.gan]
    e2 = [STEM_TO_ELEMENT.get(str(g), "unknown") for g in p2.gan]
    same_element = sum(1 for x in e1 for y in e2 if x == y)
    gen_link = sum(1 for x in e1 for y in e2 if GEN_MAP.get(x) == y or GEN_MAP.get(y) == x)
    ctrl_link = sum(1 for x in e1 for y in e2 if CTRL_MAP.get(x) == y or CTRL_MAP.get(y) == x)

    branch_rel = _collect_branch_relations(p1.ji, p2.ji)
    tg_12 = _ten_god_label(d1, d2)
    tg_21 = _ten_god_label(d2, d1)

    ys1 = _extract_yongshin_elements(r1)
    ys2 = _extract_yongshin_elements(r2)
    yongshin_overlap = len(set(ys1) & set(ys2))

    score_oheng = min(100.0, 40.0 + gen_link * 3.0 + same_element * 1.0 - ctrl_link * 2.0)
    score_day = 85.0 if rel == "generate" else (70.0 if rel == "same" else 45.0 if rel == "control" else 60.0)
    score_tengod = 80.0 if ("정" in tg_12 or "정" in tg_21) else 62.0
    score_branch = max(20.0, 70.0 + branch_rel["combine"] * 4.0 - branch_rel["clash"] * 9.0 - branch_rel["harm"] * 4.0 - branch_rel["punish"] * 3.0)
    score_yong = min(100.0, 45.0 + yongshin_overlap * 18.0)

    score_100 = (
        score_oheng * 0.30
        + score_day * 0.20
        + score_tengod * 0.20
        + score_branch * 0.20
        + score_yong * 0.10
    )
    star = _score_to_star(score_100)

    summary = (
        f"두 분의 궁합은 {star}점대 흐름으로 보이며, 초반 끌림과 현실 조율이 함께 필요한 관계일 가능성이 큽니다. "
        "감정 표현 방식이 다를 수 있어 대화 리듬을 맞추는 것이 핵심입니다."
    )
    attraction = (
        f"일간 관계는 '{rel}' 성향으로 해석되며, 서로를 자극하거나 보완하는 지점이 있습니다. "
        f"십신 관점에서는 {tg_12}/{tg_21} 기질이 만나 역할 분담이 형성되기 쉽습니다."
    )
    conflict = (
        f"지지 관계에서 합 {branch_rel['combine']}개, 충 {branch_rel['clash']}개 패턴이 보여 "
        "기대치 불일치가 생기면 감정 소모로 번질 수 있습니다."
    )
    longevity = (
        "오래 가는 조건은 '감정 확인 + 생활 규칙 합의'입니다. "
        "문제가 생겼을 때 누가 먼저 사과할지, 돈·시간 사용 규칙을 미리 정하면 안정감이 커질 수 있습니다."
    )
    guide = (
        "주 1회 관계 점검 대화를 짧게 가지세요. 좋았던 점 1개와 불편했던 점 1개를 번갈아 말하면 "
        "오해가 누적되기 전에 조율할 수 있습니다."
    )

    return {
        "score": star,
        "score100": round(score_100, 1),
        "summary": summary,
        "attraction": attraction,
        "conflict": conflict,
        "longevity": longevity,
        "reality": {
            "emotion": "정서적 친밀감은 빠르게 형성되지만, 표현 방식 차이를 인정할 때 안정됩니다.",
            "money": "소비 성향과 우선순위 차이를 초기에 맞추면 갈등 가능성을 크게 줄일 수 있습니다.",
            "lifestyle": "생활 리듬(연락 빈도, 휴식 스타일)을 합의하면 관계 지속성이 올라갑니다.",
        },
        "guide": guide,
        "meta": {
            "gender1": gender1,
            "gender2": gender2,
            "day_stem_relation": rel,
            "ten_gods": {"to_1": tg_12, "to_2": tg_21},
            "branch_relations": branch_rel,
        },
    }

