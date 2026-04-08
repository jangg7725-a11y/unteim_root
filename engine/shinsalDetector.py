# -*- coding: utf-8 -*-
"""
shinsalDetector.py
- 신살 탐지 엔진 (12운성, 도화, 천을귀인, 괴강, 겁살/화개/재살/망신/월살/지살/천살/양인 등)
- 12운성 계산 함수: unteim/engine/shinsal_rules.py 의 twelve_lifestage()
- 외부 메타/확장: unteim/engine/data/shinsal_ext_rules.json (설명/행운색/아이템 등)
"""

from __future__ import annotations

import os
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple, Literal, TypeAlias

from .shinsal_rules import twelve_lifestage

# -------------------------------------------------------------------
# 타입
# -------------------------------------------------------------------
Where: TypeAlias = Literal["year", "month", "day", "hour"]

@dataclass
class ShinsalHit:
    name: str
    where: Where
    branch: str
    detail: str = ""
    weight: int = 1


# -------------------------------------------------------------------
# 유틸
# -------------------------------------------------------------------
def _normalize_pillars(pillars: Dict[str, Tuple[str, str]]) -> Dict[Where, Tuple[str, str]]:
    """
    pillars = {"year":("간","지"), "month":(...), "day":(...), "hour":(...)}
    """
    keys = ("year", "month", "day", "hour")
    out: Dict[Where, Tuple[str, str]] = {}
    for k in keys:
        if k not in pillars:
            raise ValueError(f"pillars에 '{k}'가 없습니다.")
        v = pillars[k]
        if not (isinstance(v, (list, tuple)) and len(v) == 2):
            raise ValueError(f"pillars['{k}'] 형식 오류: ('간','지') 이어야 합니다.")
        out[k] = (str(v[0]), str(v[1]))
    return out  # type: ignore[return-value]


def _unique_hits(hits: List[ShinsalHit]) -> List[ShinsalHit]:
    """같은 위치/같은 신살/같은 지지 중복 제거(먼저 나온 것 유지)"""
    uniq: Dict[Tuple[str, Where, str], ShinsalHit] = {}
    for h in hits:
        key = (h.name, h.where, h.branch)
        if key not in uniq:
            uniq[key] = h
    return list(uniq.values())


# -------------------------------------------------------------------
# 삼합 유틸 (역마/반안/장성, 삼살 등에 사용)
# -------------------------------------------------------------------
_TRIADS = [
    ("申", "子", "辰"),  # 수(水) 삼합
    ("寅", "午", "戌"),  # 화(火) 삼합
    ("巳", "酉", "丑"),  # 금(金) 삼합
    ("亥", "卯", "未"),  # 목(木) 삼합
]
_TRIAD_INDEX = {b: i for i, g in enumerate(_TRIADS) for b in g}

def _triad_idx(branch: str) -> int:
    return _TRIAD_INDEX.get(branch, -1)


# -------------------------------------------------------------------
# 12운성
# -------------------------------------------------------------------
def detect_12_shinsal(pillars: Dict[Where, Tuple[str, str]]) -> List[ShinsalHit]:
    """일간 기준 12운성"""
    hits: List[ShinsalHit] = []
    day_stem = pillars["day"][0]
    for where in ("year", "month", "day", "hour"):
        br = pillars[where][1]
        stage = twelve_lifestage(day_stem, br)
        if stage:
            hits.append(
                ShinsalHit(
                    name=f"12운성:{stage}",
                    where=where,
                    branch=br,
                    detail=f"일간[{day_stem}] 기준",
                    weight=1,
                )
            )
    return hits


# -------------------------------------------------------------------
# 확장 신살 (8종) - 현재는 “안전 구현” + 필요시 추후 표준화 가능
# -------------------------------------------------------------------
def detect_geobsal(pillars: Dict[Where, Tuple[str, str]]) -> List[ShinsalHit]:
    """
    겁살(劫殺): 일지와 정충(6충) 관계 지지가 다른 기둥에 있으면 히트.
    子-午, 丑-未, 寅-申, 卯-酉, 辰-戌, 巳-亥 (+역상)
    """
    results: List[ShinsalHit] = []
    day_b = pillars["day"][1]
    opposite = {
        "子": "午", "丑": "未", "寅": "申", "卯": "酉", "辰": "戌", "巳": "亥",
        "午": "子", "未": "丑", "申": "寅", "酉": "卯", "戌": "辰", "亥": "巳",
    }.get(day_b)

    if not opposite:
        return results

    for where in ("year", "month", "day", "hour"):
        if pillars[where][1] == opposite:
            results.append(
                ShinsalHit(
                    name="겁살",
                    where=where,
                    branch=opposite,
                    detail=f"일지[{day_b}] ↔ {opposite} 정충",
                    weight=1,
                )
            )
    return results


def detect_hwagae(pillars: Dict[Where, Tuple[str, str]]) -> List[ShinsalHit]:
    """
    화개살(華蓋): 일지 기준 화개 매핑(널리 쓰는 표)
    子→辰, 丑→巳, 寅→午, 卯→未, 辰→申, 巳→酉, 午→戌, 未→亥, 申→子, 酉→丑, 戌→寅, 亥→卯
    """
    results: List[ShinsalHit] = []
    day_b = pillars["day"][1]
    target = {
        "子": "辰", "丑": "巳", "寅": "午", "卯": "未", "辰": "申", "巳": "酉",
        "午": "戌", "未": "亥", "申": "子", "酉": "丑", "戌": "寅", "亥": "卯",
    }.get(day_b)

    if not target:
        return results

    for where in ("year", "month", "day", "hour"):
        if pillars[where][1] == target:
            results.append(
                ShinsalHit(
                    name="화개살",
                    where=where,
                    branch=target,
                    detail=f"일지[{day_b}] 기준 화개",
                    weight=1,
                )
            )
    return results


def detect_jaesal(pillars: Dict[Where, Tuple[str, str]]) -> List[ShinsalHit]:
    """재살(災殺): (현재 임시 매핑)"""
    hits: List[ShinsalHit] = []
    day_b = pillars["day"][1]
    mapping = {"寅": "申", "申": "寅", "巳": "亥", "亥": "巳"}
    target = mapping.get(day_b)
    if target:
        for where in ("year", "month", "hour"):
            if pillars[where][1] == target:
                hits.append(
                    ShinsalHit(
                        name="재살",
                        where=where,
                        branch=target,
                        detail=f"일지 {day_b} ↔ {target} 충",
                        weight=1,
                    )
                )
    return hits


def detect_mangsin(pillars: Dict[Where, Tuple[str, str]]) -> List[ShinsalHit]:
    """망신살(亡神): (현재 임시 매핑)"""
    hits: List[ShinsalHit] = []
    day_b = pillars["day"][1]
    mapping = {"寅": "巳", "巳": "申", "申": "亥", "亥": "寅"}
    target = mapping.get(day_b)
    if target:
        for where in ("year", "month", "hour"):
            if pillars[where][1] == target:
                hits.append(
                    ShinsalHit(
                        name="망신살",
                        where=where,
                        branch=target,
                        detail=f"일지 {day_b} ↔ {target} 망신",
                        weight=1,
                    )
                )
    return hits


def detect_wolssal(pillars: Dict[Where, Tuple[str, str]]) -> List[ShinsalHit]:
    """월살(月殺): (현재 임시 매핑)"""
    hits: List[ShinsalHit] = []
    month_b = pillars["month"][1]
    mapping = {"寅": "子", "卯": "丑", "申": "午", "酉": "未"}
    target = mapping.get(month_b)
    if target:
        for where in ("day", "hour"):
            if pillars[where][1] == target:
                hits.append(
                    ShinsalHit(
                        name="월살",
                        where=where,
                        branch=target,
                        detail=f"월지 {month_b} ↔ {target} 월살",
                        weight=1,
                    )
                )
    return hits


def detect_jisal(pillars: Dict[Where, Tuple[str, str]]) -> List[ShinsalHit]:
    """지살(地殺): (현재 임시 매핑)"""
    hits: List[ShinsalHit] = []
    mapping = {"寅": "辰", "申": "戌", "巳": "丑", "亥": "未"}
    day_b = pillars["day"][1]
    target = mapping.get(day_b)
    if target:
        for where in ("year", "month", "hour"):
            if pillars[where][1] == target:
                hits.append(
                    ShinsalHit(
                        name="지살",
                        where=where,
                        branch=target,
                        detail=f"일지 {day_b} ↔ {target} 지살",
                        weight=1,
                    )
                )
    return hits


def detect_cheonsal(pillars: Dict[Where, Tuple[str, str]]) -> List[ShinsalHit]:
    """천살(天殺): (현재 임시 매핑)"""
    hits: List[ShinsalHit] = []
    mapping = {"寅": "戌", "卯": "亥", "申": "辰", "酉": "巳"}
    year_b = pillars["year"][1]
    target = mapping.get(year_b)
    if target:
        for where in ("day", "hour"):
            if pillars[where][1] == target:
                hits.append(
                    ShinsalHit(
                        name="천살",
                        where=where,
                        branch=target,
                        detail=f"연지 {year_b} ↔ {target} 천살",
                        weight=1,
                    )
                )
    return hits


def detect_yangin(pillars: Dict[Where, Tuple[str, str]]) -> List[ShinsalHit]:
    """
    양인살(羊刃): 12운성 엔진 기준 '제왕(帝旺)' 지지가 기둥에 존재하면 히트.
    (학파차 최소화: twelve_lifestage를 기준으로 통일)
    """
    hits: List[ShinsalHit] = []
    day_stem = pillars["day"][0]
    for where in ("year", "month", "day", "hour"):
        br = pillars[where][1]
        stage = twelve_lifestage(day_stem, br)
        if stage in ("帝旺", "제왕"):
            hits.append(
                ShinsalHit(
                    name="양인살",
                    where=where,
                    branch=br,
                    detail=f"일간[{day_stem}]의 12운성 '제왕' 지지",
                    weight=1,
                )
            )
    return hits


def detect_baekho(pillars: Dict[Where, Tuple[str, str]]) -> List[ShinsalHit]:
    """백호살(白虎殺): (현재 임시 매핑)"""
    hits: List[ShinsalHit] = []
    mapping = {"寅": "戌", "巳": "丑", "申": "辰", "亥": "未"}
    day_b = pillars["day"][1]
    target = mapping.get(day_b)
    if target:
        for where in ("month", "hour"):
            if pillars[where][1] == target:
                hits.append(
                    ShinsalHit(
                        name="백호살",
                        where=where,
                        branch=target,
                        detail=f"일지 {day_b} ↔ {target} 백호",
                        weight=1,
                    )
                )
    return hits


def detect_suok(pillars: Dict[Where, Tuple[str, str]]) -> List[ShinsalHit]:
    """수옥살(囚獄殺): (현재 간단 예시)"""
    hits: List[ShinsalHit] = []
    pairs = [("子", "午"), ("卯", "酉")]
    for (a, b) in pairs:
        if pillars["day"][1] == a:
            for where in ("year", "month", "hour"):
                if pillars[where][1] == b:
                    hits.append(
                        ShinsalHit(
                            name="수옥살",
                            where=where,
                            branch=b,
                            detail=f"{a} ↔ {b} 수옥",
                            weight=1,
                        )
                    )
    return hits


def detect_banan_yeokma_jangseong(pillars: Dict[Where, Tuple[str, str]]) -> List[ShinsalHit]:
    """
    12신살 계열(반안/역마/장성/재살) 보강.
    - 기준: 연지 삼합 그룹
    - 앱 스타일 결과와의 호환을 위해 보수적으로 운용
    """
    hits: List[ShinsalHit] = []
    year_b = pillars["year"][1]
    # 그룹별 타깃(실무 호환 테이블)
    tables = {
        "寅午戌": {"반안살": "丑", "역마살": "申", "장성살": "子", "재살": "午"},
        "申子辰": {"반안살": "未", "역마살": "寅", "장성살": "辰", "재살": "子"},
        "巳酉丑": {"반안살": "戌", "역마살": "亥", "장성살": "酉", "재살": "卯"},
        "亥卯未": {"반안살": "辰", "역마살": "巳", "장성살": "卯", "재살": "酉"},
    }
    group_key = next((g for g in tables if year_b in g), "")
    if not group_key:
        return hits
    mapping = tables[group_key]
    for where in ("year", "month", "day", "hour"):
        br = pillars[where][1]
        for name, tgt in mapping.items():
            if br == tgt:
                hits.append(
                    ShinsalHit(
                        name=name,
                        where=where,
                        branch=br,
                        detail=f"연지[{year_b}] 그룹({group_key}) 기준",
                        weight=1,
                    )
                )
    return hits


def detect_taeguk_cheonju_amrok_sangmun(pillars: Dict[Where, Tuple[str, str]]) -> List[ShinsalHit]:
    """실무에서 자주 보는 보강 길/흉신 세트."""
    hits: List[ShinsalHit] = []
    day_g, day_b = pillars["day"]
    year_b = pillars["year"][1]

    taeguk_map = {
        "甲": {"子", "午"}, "乙": {"子", "午"},
        "丙": {"卯", "酉"}, "丁": {"卯", "酉"},
        "戊": {"丑", "未"}, "己": {"丑", "未"},
        "庚": {"寅", "申"}, "辛": {"寅", "申"},
        "壬": {"辰", "戌"}, "癸": {"辰", "戌"},
    }
    cheonju_map = {
        "甲": {"寅"}, "乙": {"卯"}, "丙": {"巳"}, "丁": {"午"},
        "戊": {"申"}, "己": {"酉"}, "庚": {"亥"}, "辛": {"子"},
        "壬": {"寅"}, "癸": {"卯"},
    }
    amrok_map = {
        "甲": {"寅"}, "乙": {"卯"}, "丙": {"巳"}, "丁": {"午"},
        "戊": {"申"}, "己": {"酉"}, "庚": {"亥"}, "辛": {"子"},
        "壬": {"寅"}, "癸": {"卯"},
    }
    sangmun_map = {
        "子": "酉", "丑": "戌", "寅": "亥", "卯": "子", "辰": "丑", "巳": "寅",
        "午": "卯", "未": "辰", "申": "巳", "酉": "午", "戌": "未", "亥": "申",
    }

    for where in ("year", "month", "day", "hour"):
        br = pillars[where][1]
        if br in taeguk_map.get(day_g, set()):
            hits.append(ShinsalHit(name="태극귀인", where=where, branch=br, detail=f"일간[{day_g}] 기준", weight=1))
        if br in cheonju_map.get(day_g, set()):
            hits.append(ShinsalHit(name="천주귀인", where=where, branch=br, detail=f"일간[{day_g}] 기준", weight=1))
        if br in amrok_map.get(day_g, set()):
            hits.append(ShinsalHit(name="암록", where=where, branch=br, detail=f"일간[{day_g}] 기준", weight=1))
        if br == sangmun_map.get(year_b):
            hits.append(ShinsalHit(name="상문살", where=where, branch=br, detail=f"연지[{year_b}] 기준", weight=-1))
        # 문창귀인(간단 보강): 일지와 같은 삼합 그룹의 핵심 지지
        if _triad_idx(br) == _triad_idx(day_b) and br != day_b:
            hits.append(ShinsalHit(name="문창귀인", where=where, branch=br, detail=f"일지[{day_b}] 삼합 연동", weight=1))

    return hits


# -------------------------------------------------------------------
# 핵심 신살 (도화/천을귀인/괴강)
# -------------------------------------------------------------------
_TAOHUA_TABLE = {"子": "卯", "午": "酉", "卯": "子", "酉": "午"}

def detect_taohua(pillars: Dict[Where, Tuple[str, str]]) -> List[ShinsalHit]:
    hits: List[ShinsalHit] = []
    day_b = pillars["day"][1]
    taohua = _TAOHUA_TABLE.get(day_b)
    if not taohua:
        return hits
    for where in ("year", "month", "day", "hour"):
        br = pillars[where][1]
        if br == taohua:
            hits.append(
                ShinsalHit(
                    name="도화",
                    where=where,
                    branch=br,
                    detail=f"일지[{day_b}] 기준 도화",
                    weight=1,
                )
            )
    return hits


def detect_teneul(pillars: Dict[Where, Tuple[str, str]]) -> List[ShinsalHit]:
    """
    천을귀인(天乙貴人): 일간 기준 전통 2지지 표(현재 사용 중인 버전 유지)
    """
    hits: List[ShinsalHit] = []
    day_g = pillars["day"][0]
    # data/shinsal_rules.json(TIANYI_GUIREN_*)과 동일 표준표 사용
    teneul_map = {
        "甲": ["丑", "未"], "乙": ["子", "申"], "丙": ["亥", "酉"], "丁": ["酉", "亥"],
        "戊": ["丑", "未"], "己": ["子", "申"], "庚": ["巳", "卯"], "辛": ["卯", "巳"],
        "壬": ["午", "寅"], "癸": ["寅", "午"],
    }
    targets = teneul_map.get(day_g, [])
    if not targets:
        return hits
    for where in ("year", "month", "day", "hour"):
        br = pillars[where][1]
        if br in targets:
            hits.append(
                ShinsalHit(
                    name="천을귀인",
                    where=where,
                    branch=br,
                    detail=f"일간[{day_g}]의 천을귀인 지지",
                    weight=2,  # 길신 가중치
                )
            )
    return hits


_GOEGANG_SET = {
    ("庚", "辰"), ("庚", "戌"), ("辛", "丑"), ("辛", "未"),
    ("壬", "辰"), ("壬", "戌"), ("癸", "丑"), ("癸", "未"),
}

def detect_goegang(pillars: Dict[Where, Tuple[str, str]], include_optional: bool = False) -> List[ShinsalHit]:
    hits: List[ShinsalHit] = []
    ds, db = pillars["day"]
    if (ds, db) in _GOEGANG_SET:
        hits.append(ShinsalHit(name="괴강살", where="day", branch=db, detail=f"일주[{ds}{db}]", weight=2))
    if include_optional:
        for where in ("year", "month", "hour"):
            s, b = pillars[where]
            if (s, b) in _GOEGANG_SET:
                hits.append(
                    ShinsalHit(
                        name="괴강살(확장)",
                        where=where,
                        branch=b,
                        detail=f"{where}주[{s}{b}]",
                        weight=1,
                    )
                )
    return hits


# -------------------------------------------------------------------
# 확장 룰 자리(현재 빈)
# -------------------------------------------------------------------
def detect_ext_rules(pillars: Dict[Where, Tuple[str, str]]) -> List[ShinsalHit]:
    return []


def detect_rules_json_catalog(pillars: Dict[Where, Tuple[str, str]]) -> List[ShinsalHit]:
    """
    data/shinsal_rules.json 규칙을 이용한 보강 탐지.
    - 귀인류(천/월덕/태극/문창/복성 등) 확장을 우선 목표로 사용.
    - 규칙 포맷: match_any.stems / match_any.branches
    """
    rules_path = Path(__file__).resolve().parent.parent / "data" / "shinsal_rules.json"
    if not rules_path.exists():
        return []
    try:
        raw = json.loads(rules_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    rules = raw.get("rules") if isinstance(raw, dict) else None
    if not isinstance(rules, list):
        return []

    scope_val = {
        "year_gan": pillars["year"][0], "year_ji": pillars["year"][1],
        "month_gan": pillars["month"][0], "month_ji": pillars["month"][1],
        "day_gan": pillars["day"][0], "day_ji": pillars["day"][1],
        "hour_gan": pillars["hour"][0], "hour_ji": pillars["hour"][1],
    }
    scope_where = {
        "year_gan": "year", "year_ji": "year",
        "month_gan": "month", "month_ji": "month",
        "day_gan": "day", "day_ji": "day",
        "hour_gan": "hour", "hour_ji": "hour",
    }

    out: List[ShinsalHit] = []
    for r in rules:
        if not isinstance(r, dict):
            continue
        name = str(r.get("name") or "").strip()
        if not name:
            continue
        # "천을귀인(甲)" -> "천을귀인"
        if "(" in name:
            name = name.split("(", 1)[0].strip()
        ma = r.get("match_any")
        if not isinstance(ma, dict):
            continue

        stems = ma.get("stems") if isinstance(ma.get("stems"), dict) else None
        brs = ma.get("branches") if isinstance(ma.get("branches"), dict) else None

        stem_ok = True
        stem_hit_where: List[Where] = []
        if stems:
            any_of = set(str(x) for x in (stems.get("any_of") or []))
            scopes = [str(x) for x in (stems.get("scope") or [])]
            stem_ok = any(scope_val.get(sc) in any_of for sc in scopes)
            stem_hit_where = [scope_where[sc] for sc in scopes if scope_val.get(sc) in any_of and sc in scope_where]

        branch_hit_where: List[Where] = []
        if brs:
            any_of = set(str(x) for x in (brs.get("any_of") or []))
            scopes = [str(x) for x in (brs.get("scope") or [])]
            branch_hit_where = [scope_where[sc] for sc in scopes if scope_val.get(sc) in any_of and sc in scope_where]

        if not stem_ok:
            continue

        targets: List[Where]
        if branch_hit_where:
            targets = branch_hit_where
        elif stem_hit_where:
            targets = stem_hit_where
        else:
            continue

        w = 2 if "귀인" in name else 1
        for where in targets:
            out.append(
                ShinsalHit(
                    name=name,
                    where=where,
                    branch=pillars[where][1],
                    detail="shinsal_rules.json",
                    weight=w,
                )
            )
    return out


# -------------------------------------------------------------------
# 메인 엔트리
# -------------------------------------------------------------------
def detect_shinsal(
    pillars: Dict[str, Tuple[str, str]],
    *,
    include_optional_goegang: bool = False,
    include_ext_rules: bool = True,
) -> Dict[str, Any]:
    P = _normalize_pillars(pillars)
    results: List[ShinsalHit] = []

    # 12운성
    results += detect_12_shinsal(P)

    # 확장(8종)
    results += detect_geobsal(P)
    results += detect_hwagae(P)
    results += detect_jaesal(P)
    results += detect_mangsin(P)
    results += detect_wolssal(P)
    results += detect_jisal(P)
    results += detect_cheonsal(P)
    results += detect_yangin(P)
    results += detect_baekho(P)
    results += detect_suok(P)
    results += detect_banan_yeokma_jangseong(P)
    results += detect_taeguk_cheonju_amrok_sangmun(P)

    # 핵심
    results += detect_taohua(P)
    results += detect_teneul(P)
    results += detect_goegang(P, include_optional_goegang)

    # 확장 룰(JSON/CSV)
    if include_ext_rules:
        results += detect_ext_rules(P)
    results += detect_rules_json_catalog(P)

        # 중복 정리
    results = _unique_hits(results)

    # 점수 요약
    summary = score_shinsal(results)

    # dict 변환
    items = [
        {"name": h.name, "where": h.where, "branch": h.branch, "detail": h.detail, "weight": h.weight}
        for h in results
    ]

    return {
        "items": items,
        "summary": summary,
    }


def score_shinsal(hits: List[ShinsalHit]) -> Dict[str, Any]:
    """
    신살 결과(ShinsalHit 리스트)를 점수로 합산해 요약.
    - 기본 규칙:
      * weight > 0 : 길신 점수(+)
      * weight < 0 : 흉신 점수(-)
      * weight == 0: 중립
    - 최종 판정:
      * total >= +3  -> "길"
      * -2 ~ +2      -> "중립"
      * total <= -3  -> "주의"
    """
    by_where: Dict[str, Dict[str, int]] = {
        "year": {"good": 0, "bad": 0, "total": 0},
        "month": {"good": 0, "bad": 0, "total": 0},
        "day": {"good": 0, "bad": 0, "total": 0},
        "hour": {"good": 0, "bad": 0, "total": 0},
    }

    good_total = 0
    bad_total = 0

    for h in hits:
        w = int(getattr(h, "weight", 0) or 0)
        if w > 0:
            good_total += w
            by_where[h.where]["good"] += w
        elif w < 0:
            bad_total += w  # 음수로 누적
            by_where[h.where]["bad"] += w
        by_where[h.where]["total"] += w

    total = good_total + bad_total  # bad_total은 음수

    if total >= 3:
        verdict = "길"
    elif total <= -3:
        verdict = "주의"
    else:
        verdict = "중립"

    return {
        "good_total": good_total,
        "bad_total": bad_total,
        "total": total,
        "verdict": verdict,
        "by_where": by_where,
    }


# -------------------------------------------------------------------
# 보강: 메타(설명/행운색/아이템) 적용 + 리포트 요약
# -------------------------------------------------------------------
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "shinsal_ext_rules.json")
EXPLAIN_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "shinsal_explanations.json")

def _load_shinsal_meta(path: str = DATA_PATH) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Shinsal meta JSON not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_shinsal_explain(path: str = EXPLAIN_PATH) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict):
            return raw
    except Exception:
        return {}
    return {}


def _enrich_shinsal_result(
    raw_result: Dict[str, List[str]],
    meta: Dict[str, Any],
    explain: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    by_pillar = {k: [] for k in ["year", "month", "day", "hour"]}
    flat_list: List[Dict[str, Any]] = []
    colors, directions, items = set(), set(), set()

    for pillar, names in raw_result.items():
        for name in names:
            data = meta.get(name, {})
            ex = (explain or {}).get(name, {})
            enriched = {
                "name": name,
                "element": data.get("element"),
                "description": data.get("description", "") or ex.get("summary", ""),
                "advice": data.get("advice", ""),
                "lucky_color": data.get("lucky_color", []),
                "lucky_direction": data.get("lucky_direction", []),
                "lucky_items": data.get("lucky_items", []),
                "affirmation": data.get("affirmation", ""),
                "keywords": ex.get("keywords", []),
            }
            colors.update(enriched["lucky_color"])
            directions.update(enriched["lucky_direction"])
            items.update(enriched["lucky_items"])
            by_pillar.setdefault(pillar, []).append(enriched)
            flat_list.append(enriched)

    return {
        "by_pillar": by_pillar,
        "flat_list": flat_list,
        "recommendation_bundle": {
            "colors": sorted(colors),
            "directions": sorted(directions),
            "items": sorted(items),
        },
    }


def _summarize_for_report(enriched: Dict[str, Any]) -> Dict[str, Any]:
    lines: List[str] = []
    names_kr = {"year": "년주", "month": "월주", "day": "일주", "hour": "시주"}
    for pillar in ["year", "month", "day", "hour"]:
        for e in enriched["by_pillar"].get(pillar, []):
            color = ", ".join(e.get("lucky_color", []))
            item = ", ".join(e.get("lucky_items", []))
            lines.append(
                f"• {names_kr[pillar]} {e['name']}: {e['description']} (행운색: {color} / 아이템: {item})"
            )
    return {"summary_text": "\n".join(lines), "bundle": enriched["recommendation_bundle"]}


_PILLAR_ALIAS = {
    "y": "year", "yr": "year", "year": "year",
    "m": "month", "mo": "month", "month": "month",
    "d": "day", "day": "day",
    "h": "hour", "hr": "hour", "hour": "hour",
}

def _coerce_raw_result(raw: Any) -> Dict[str, List[str]]:
    """
    다양한 결과 형태를 {"year":[...],"month":[...],"day":[...],"hour":[...]} 로 통일
    - detect_shinsal() 표준: {"items": List[{"name","where",...}], "summary": ...}
    - 구형: List[{"name","where","branch","detail"}]
    """
    out = {"year": [], "month": [], "day": [], "hour": []}

    if isinstance(raw, dict) and "items" in raw:
        inner = raw.get("items")
        if isinstance(inner, list):
            return _coerce_raw_result(inner)

    # 1) detect_shinsal 표준(List[Dict]) 대응
    if isinstance(raw, list) and raw and isinstance(raw[0], dict) and "name" in raw[0] and ("where" in raw[0] or "pillar" in raw[0]):
        for x in raw:
            w = x.get("where") or x.get("pillar")
            name = x.get("name")
            if not name:
                continue
            pk = _PILLAR_ALIAS.get(str(w).lower(), str(w)) if w else "day"
            if pk not in out:
                pk = "day"
            out[pk].append(name)
        return out

    # 2) dict 패턴: {"year":[...], ...}
    if isinstance(raw, dict):
        for k, v in raw.items():
            pk = _PILLAR_ALIAS.get(str(k).lower(), str(k))
            if pk not in out:
                continue
            if isinstance(v, list):
                out[pk].extend([str(i) for i in v])
            else:
                out[pk].append(str(v))
        return out

    # 3) list 패턴: [("year","천덕귀인"), ...] / ["도화", ...]
    if isinstance(raw, list):
        for x in raw:
            if isinstance(x, tuple) and len(x) == 2:
                pk = _PILLAR_ALIAS.get(str(x[0]).lower(), "day")
                if pk not in out:
                    pk = "day"
                out[pk].append(str(x[1]))
            elif isinstance(x, str):
                out["day"].append(x)
        return out

    return out


def analyze_shinsal_with_enrichment(pillars: Dict[str, Any]) -> Dict[str, Any]:
    """
    외부 공개 함수:
    (detect_shinsal 결과) -> (메타 적용) -> (리포트 요약)
    """
    meta = _load_shinsal_meta()
    explain = _load_shinsal_explain()
    raw = detect_shinsal(pillars)
    raw2 = _coerce_raw_result(raw)
    enriched = _enrich_shinsal_result(raw2, meta, explain)
    report = _summarize_for_report(enriched)
    return {"raw": raw2, "enriched": enriched, "report": report}


def normalize_shinsal_result(sh: Any) -> Dict[str, Any]:
    """결과를 dict 형태로 통일"""
    if isinstance(sh, dict):
        return sh
    if isinstance(sh, list):
        return {"all": sh}
    return {"all": [sh]}


if __name__ == "__main__":
    sample = {
        "year": ("丙", "午"),
        "month": ("庚", "子"),
        "day": ("戊", "申"),
        "hour": ("癸", "丑"),
    }
    out = detect_shinsal(sample)
    for x in out.get("items", []):
        print(x)
