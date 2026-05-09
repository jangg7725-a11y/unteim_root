# engine/shinsal_psychology_interpreter.py
# -*- coding: utf-8 -*-
"""
신살(神煞) → 심리/행동 패턴 슬롯 변환기

shinsalDetector.py / shinsal_explainer.py 가 탐지한 신살 이름을
narrative/shinsal_psychology_db.json 에서 조회해
dominant_trait / behavior_pattern / inner_state / relation_pattern /
reframe / caution 슬롯을 반환한다.

사용법:
    from engine.shinsal_psychology_interpreter import get_shinsal_psychology_slots
    slots = get_shinsal_psychology_slots(packed)
    # slots["items"][0]["behavior_pattern"] 등
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from utils.narrative_loader import load_sentences

# ──────────────────────────────────────────────
# 1) DB 로드
# ──────────────────────────────────────────────
_DB_FILE = "shinsal_psychology_db"


def _db() -> Dict[str, Any]:
    return load_sentences(_DB_FILE)


def _patterns() -> Dict[str, Any]:
    return _db().get("shinsal_patterns", {})


# ──────────────────────────────────────────────
# 2) 신살 이름 → DB 키 변환
# ──────────────────────────────────────────────
def _key_map() -> Dict[str, str]:
    return _db().get("engine_mapping", {}).get("key_map", {})


def _resolve_key(shinsal_name: str) -> Optional[str]:
    """
    '역마', '역마살', 'YEOKMA' 등 다양한 형태를 DB 키로 정규화.
    """
    name = str(shinsal_name).strip()
    kmap = _key_map()

    # 직접 매핑
    if name in kmap:
        return kmap[name]

    # DB 키 직접 일치 (역마살 등)
    pats = _patterns()
    if name in pats:
        return name

    # '살' 붙이거나 떼서 재시도
    variants = [name + "살", name.rstrip("살"), name.replace("귀인", "")]
    for v in variants:
        if v in kmap:
            return kmap[v]
        if v in pats:
            return v

    return None


# ──────────────────────────────────────────────
# 3) packed dict 에서 신살 목록 추출
# ──────────────────────────────────────────────
def _extract_shinsal_names(packed: Dict[str, Any]) -> List[str]:
    """
    packed 에서 탐지된 신살 이름 리스트를 추출.

    지원하는 구조:
        packed["shinsal"]["items"] = [{"name": "역마살"}, ...]
        packed["shinsal"]["names"] = ["역마살", ...]
        packed["shinsal_list"] = ["역마살", ...]
        packed["analysis"]["shinsal"] = [...]
    """
    names: List[str] = []

    def _harvest(val: Any) -> None:
        if isinstance(val, list):
            for v in val:
                if isinstance(v, str) and v:
                    names.append(v)
                elif isinstance(v, dict):
                    for k in ("name", "label", "code", "id"):
                        if isinstance(v.get(k), str) and v[k]:
                            names.append(v[k])
                            break
        elif isinstance(val, dict):
            for k in ("name", "label", "names", "items"):
                _harvest(val.get(k))
        elif isinstance(val, str) and val:
            names.append(val)

    candidates = [
        packed.get("shinsal"),
        packed.get("shinsal_list"),
        packed.get("analysis", {}).get("shinsal"),
        packed.get("shinsal_result"),
    ]
    for c in candidates:
        if c is not None:
            _harvest(c)

    # 중복 제거 (순서 유지)
    seen: set = set()
    unique: List[str] = []
    for n in names:
        if n not in seen:
            seen.add(n)
            unique.append(n)
    return unique


# ──────────────────────────────────────────────
# 4) 슬롯 선택 유틸
# ──────────────────────────────────────────────
def _pick(pool: Any, seed: Optional[int] = None) -> str:
    if isinstance(pool, str):
        return pool
    if isinstance(pool, list) and pool:
        return random.Random(seed).choice(pool)
    return ""


# ──────────────────────────────────────────────
# 5) 신살 아이템 → 슬롯 dict
# ──────────────────────────────────────────────
def _build_slots(
    key: str,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    pat = _patterns().get(key, {})
    if not pat:
        return {}

    profile = pat.get("psychological_profile", {})

    return {
        "shinsal_id": key,
        "label_ko": pat.get("label_ko", ""),
        "category": pat.get("category", "neutral"),
        "core_theme": pat.get("core_theme", ""),
        # 심리 프로파일 슬롯
        "dominant_trait": profile.get("dominant_trait", ""),
        "behavior_pattern": _pick(profile.get("behavior_pattern", []), seed),
        "inner_state": _pick(profile.get("inner_state", []), seed),
        "stress_response": profile.get("stress_response", ""),
        # 관계 패턴
        "relation_pattern": _pick(pat.get("relation_pattern", []), seed),
        # 맥락
        "strength_context": _pick(pat.get("strength_context", []), seed),
        "friction_context": _pick(pat.get("friction_context", []), seed),
        # 리프레임 / 주의
        "reframe": _pick(pat.get("reframe", []), seed),
        "caution": pat.get("caution", ""),
    }


# ──────────────────────────────────────────────
# 6) 조합 힌트
# ──────────────────────────────────────────────
def _get_combination_hint(keys: List[str]) -> str:
    """발현된 신살 조합에 맞는 힌트를 반환."""
    combo_rules: Dict[str, Any] = _db().get("combination_rules", {})
    key_set = set(keys)

    for combo_key, rule in combo_rules.items():
        combo_parts = set(combo_key.split("+"))
        if combo_parts.issubset(key_set):
            return rule.get("hint", "")
    return ""


# ──────────────────────────────────────────────
# 7) 메인 공개 API
# ──────────────────────────────────────────────
def get_shinsal_psychology_slots(
    packed: Dict[str, Any],
    *,
    seed: Optional[int] = None,
    max_items: int = 3,
) -> Dict[str, Any]:
    """
    packed dict 를 받아 발현 신살의 심리 패턴 슬롯을 반환한다.

    반환 형태:
    {
        "found": bool,
        "items": [
            {
                "shinsal_id": "역마살",
                "label_ko": "역마살",
                "dominant_trait": "...",
                "behavior_pattern": "...",
                "inner_state": "...",
                "relation_pattern": "...",
                "reframe": "...",
                "caution": "...",
                ...
            },
            ...
        ],
        "combination_hint": "...",   # 복수 신살 조합 힌트
        # 대표 슬롯 (첫 번째)
        "dominant_trait": "...",
        "behavior_pattern": "...",
        "inner_state": "...",
        "relation_pattern": "...",
        "reframe": "...",
        "caution": "...",
    }
    """
    raw_names = _extract_shinsal_names(packed)
    result_items: List[Dict[str, Any]] = []
    resolved_keys: List[str] = []

    for name in raw_names:
        key = _resolve_key(name)
        if not key:
            continue
        slots = _build_slots(key, seed)
        if slots:
            result_items.append(slots)
            resolved_keys.append(key)
        if len(result_items) >= max_items:
            break

    found = bool(result_items)
    top = result_items[0] if found else {}
    combo_hint = _get_combination_hint(resolved_keys) if len(resolved_keys) >= 2 else ""

    return {
        "found": found,
        "items": result_items,
        "combination_hint": combo_hint,
        # 대표 슬롯
        "dominant_trait": top.get("dominant_trait", ""),
        "behavior_pattern": top.get("behavior_pattern", ""),
        "inner_state": top.get("inner_state", ""),
        "relation_pattern": top.get("relation_pattern", ""),
        "reframe": top.get("reframe", ""),
        "caution": top.get("caution", ""),
    }


def get_shinsal_slots_by_name(
    shinsal_name: str,
    *,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    신살 이름을 직접 지정해 슬롯을 꺼낼 때.
    예: get_shinsal_slots_by_name("역마살")
    """
    key = _resolve_key(shinsal_name)
    if not key:
        return {}
    return _build_slots(key, seed)
