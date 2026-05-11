# engine/hap_chung_interpreter.py
# -*- coding: utf-8 -*-
"""
합·충·형·파·해 관계 작용 → 심리/행동 패턴 슬롯 변환기

wolwoon_feature_calc.py 가 탐지한 CHUNG/HAP/HYEONG/PA/HAE 결과를
narrative/hap_chung_pattern_db.json 에서 조회해
behavior_pattern / inner_state / relation_pattern / reframe / caution 슬롯을 반환한다.

사용법:
    from engine.hap_chung_interpreter import get_relation_pattern_slots
    slots = get_relation_pattern_slots(packed)
    # slots["behavior_pattern"], slots["inner_state"], ...
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from utils.narrative_loader import load_sentences

# ──────────────────────────────────────────────
# 1) DB 로드
# ──────────────────────────────────────────────
_DB_FILE = "hap_chung_pattern_db"


def _db() -> Dict[str, Any]:
    return load_sentences(_DB_FILE)


# ──────────────────────────────────────────────
# 2) 지지 한자 → 한글 변환 테이블
# ──────────────────────────────────────────────
_BRANCH_KR: Dict[str, str] = {
    "子": "자", "丑": "축", "寅": "인", "卯": "묘",
    "辰": "진", "巳": "사", "午": "오", "未": "미",
    "申": "신", "酉": "유", "戌": "술", "亥": "해",
}


def _to_kr(branch: str) -> str:
    return _BRANCH_KR.get(branch, branch)


# ──────────────────────────────────────────────
# 3) 페어 → DB 아이템 조회
# ──────────────────────────────────────────────
_TYPE_KEYS = ("chung", "hap", "hyeong", "pa", "hae")


def _find_item(
    relation_type: str,
    pair: Tuple[str, str],
) -> Optional[Dict[str, Any]]:
    """
    relation_type: 'chung' | 'hap' | 'hyeong' | 'pa' | 'hae'
    pair: 지지 한글 2글자 튜플, 예 ('자', '오')
    """
    db = _db()
    section = db.get(relation_type, {})
    items: List[Dict[str, Any]] = section.get("items", [])

    pair_set = set(pair)
    for item in items:
        item_pair = set(item.get("pair", []))
        if pair_set == item_pair:
            return item
        # 삼형(triad)도 처리
        triad = set(item.get("triad", []))
        if triad and pair_set.issubset(triad):
            return item
    return None


# ──────────────────────────────────────────────
# 4) packed dict 에서 충합 신호 추출
# ──────────────────────────────────────────────
def _extract_relation_signals(
    packed: Dict[str, Any],
) -> List[Tuple[str, Tuple[str, str]]]:
    """
    packed['wolwoon'] 또는 packed['analysis'] 구조에서
    [(relation_type, (branch_a, branch_b)), ...] 형태로 추출.

    wolwoon_feature_calc.py 가 feature dict 에 기록하는 키를 읽는다.
        feature["chung_pair"]  = ("자", "오")  (있을 때)
        feature["hap_pair"]    = ("자", "축")
        feature["hyeong_pair"] = ...
        feature["pa_pair"]     = ...
        feature["hae_pair"]    = ...

    또한 flow_interactions_v1.py 가 생성하는 구조도 지원:
        packed["flow"]["interactions"] = [
            {"type": "CLASH", "branch_a": "자", "branch_b": "오"}, ...
        ]
    """
    signals: List[Tuple[str, Tuple[str, str]]] = []

    # ── 방법 A: wolwoon features dict ──
    _wolwoon = packed.get("wolwoon", {})
    if not isinstance(_wolwoon, dict):
        _wolwoon = {}
    features: Dict[str, Any] = (
        _wolwoon.get("features", {})
        or packed.get("features", {})
        or {}
    )
    for rtype in _TYPE_KEYS:
        key = f"{rtype}_pair"
        val = features.get(key)
        if isinstance(val, (list, tuple)) and len(val) == 2:
            a, b = _to_kr(str(val[0])), _to_kr(str(val[1]))
            signals.append((rtype, (a, b)))

    # ── 방법 B: flow interactions ──
    _TYPE_LABEL_MAP = {
        "CLASH": "chung",
        "BOOST": "hap",
        "DRAIN": "hae",
        "AMPLIFY": "hap",
    }
    interactions: List[Dict[str, Any]] = (
        (packed.get("flow") or {}).get("interactions", [])
        or []
    )
    for ix in interactions:
        label = _TYPE_LABEL_MAP.get(ix.get("type", ""), "")
        ba = _to_kr(ix.get("branch_a", ""))
        bb = _to_kr(ix.get("branch_b", ""))
        if label and ba and bb:
            signals.append((label, (ba, bb)))

    # ── 방법 C: monthly_patterns chung/hap flags ──
    mp: Dict[str, Any] = (
        packed.get("monthly_pattern", {})
        or packed.get("monthly_patterns", {})
        or {}
    )
    for rtype in ("chung", "hap"):
        flag_key = f"has_{rtype}"
        pair_key = f"{rtype}_pair"
        if mp.get(flag_key) and mp.get(pair_key):
            val = mp[pair_key]
            if isinstance(val, (list, tuple)) and len(val) == 2:
                a, b = _to_kr(str(val[0])), _to_kr(str(val[1]))
                signals.append((rtype, (a, b)))

    # 중복 제거 (같은 타입+페어)
    seen: set = set()
    unique: List[Tuple[str, Tuple[str, str]]] = []
    for rtype, pair in signals:
        key = (rtype, frozenset(pair))
        if key not in seen:
            seen.add(key)
            unique.append((rtype, pair))

    return unique


# ──────────────────────────────────────────────
# 5) 슬롯 선택 유틸
# ──────────────────────────────────────────────
def _pick(pool: Any, seed: Optional[int] = None) -> str:
    """리스트에서 랜덤 1개, 문자열이면 그대로 반환"""
    if isinstance(pool, str):
        return pool
    if isinstance(pool, list) and pool:
        rng = random.Random(seed)
        return rng.choice(pool)
    return ""


# ──────────────────────────────────────────────
# 6) 메인 공개 API
# ──────────────────────────────────────────────
def get_relation_pattern_slots(
    packed: Dict[str, Any],
    *,
    seed: Optional[int] = None,
    max_items: int = 2,
) -> Dict[str, Any]:
    """
    packed dict 를 받아 합충형파해 패턴 슬롯을 반환한다.

    반환 형태:
    {
        "found": bool,
        "items": [
            {
                "type": "chung",
                "label": "자오충",
                "behavior_pattern": "...",
                "inner_state": "...",
                "relation_pattern": "...",
                "reframe": "...",
                "caution": "...",
                "core_dynamic": "...",
            },
            ...
        ],
        # 여러 개가 발견될 때 대표 슬롯 (첫 번째 우선)
        "behavior_pattern": "...",
        "inner_state": "...",
        "relation_pattern": "...",
        "reframe": "...",
        "caution": "...",
    }
    """
    signals = _extract_relation_signals(packed)
    result_items: List[Dict[str, Any]] = []

    for rtype, pair in signals[:max_items]:
        item = _find_item(rtype, pair)
        if not item:
            continue
        result_items.append(
            {
                "type": rtype,
                "label": item.get("label_ko", ""),
                "core_dynamic": item.get("core_dynamic", ""),
                "behavior_pattern": _pick(item.get("behavior_pattern", []), seed),
                "inner_state": _pick(item.get("inner_state", []), seed),
                "relation_pattern": _pick(item.get("relation_pattern", []), seed),
                "reframe": _pick(item.get("reframe", []), seed),
                "caution": item.get("caution", ""),
            }
        )

    found = bool(result_items)
    top = result_items[0] if found else {}

    return {
        "found": found,
        "items": result_items,
        "behavior_pattern": top.get("behavior_pattern", ""),
        "inner_state": top.get("inner_state", ""),
        "relation_pattern": top.get("relation_pattern", ""),
        "reframe": top.get("reframe", ""),
        "caution": top.get("caution", ""),
    }


def get_relation_slots_by_pair(
    relation_type: str,
    branch_a: str,
    branch_b: str,
    *,
    seed: Optional[int] = None,
) -> Dict[str, str]:
    """
    직접 관계 타입과 지지 쌍을 지정해 슬롯을 꺼낼 때 사용.
    예: get_relation_slots_by_pair("chung", "자", "오")
    """
    a, b = _to_kr(branch_a), _to_kr(branch_b)
    item = _find_item(relation_type, (a, b))
    if not item:
        return {}
    return {
        "type": relation_type,
        "label": item.get("label_ko", ""),
        "core_dynamic": item.get("core_dynamic", ""),
        "behavior_pattern": _pick(item.get("behavior_pattern", []), seed),
        "inner_state": _pick(item.get("inner_state", []), seed),
        "relation_pattern": _pick(item.get("relation_pattern", []), seed),
        "reframe": _pick(item.get("reframe", []), seed),
        "caution": item.get("caution", ""),
    }
