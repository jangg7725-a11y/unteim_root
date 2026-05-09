# engine/kongmang_pattern_interpreter.py
# -*- coding: utf-8 -*-
"""
공망 위치(주) → 심리·행동 패턴 슬롯

narrative/kongmang_pattern_db.json 의 pillar_patterns 를 조회해 풀당 랜덤 1문장을 선택한다.
"""

from __future__ import annotations

import random
from typing import Any, Dict, Optional

from utils.narrative_loader import load_sentences

_DB_FILE = "kongmang_pattern_db"

_PILLAR_ALIASES: Dict[str, str] = {
    "year": "year",
    "month": "month",
    "day": "day",
    "hour": "hour",
    "년": "year",
    "월": "month",
    "일": "day",
    "시": "hour",
    "년주": "year",
    "월주": "month",
    "일주": "day",
    "시주": "hour",
}


def _db() -> Dict[str, Any]:
    return load_sentences(_DB_FILE)


def _resolve_pillar(pillar: str) -> Optional[str]:
    raw = str(pillar).strip()
    if not raw:
        return None
    if raw in _PILLAR_ALIASES:
        return _PILLAR_ALIASES[raw]
    low = raw.lower()
    if low in _PILLAR_ALIASES:
        return _PILLAR_ALIASES[low]
    pmap = _db().get("engine_mapping", {}).get("pillar_map", {})
    if raw in pmap:
        return str(pmap[raw])
    if low in pmap:
        return str(pmap[low])
    patterns = _db().get("pillar_patterns", {})
    if raw in patterns:
        return raw
    if low in patterns:
        return low
    return None


def _pick_from_pool(
    pool: Any,
    rng: random.Random,
) -> str:
    if isinstance(pool, str) and pool.strip():
        return pool
    if isinstance(pool, list) and pool:
        return str(rng.choice(pool))
    return ""


def _pick_pool_fields(
    entry: Dict[str, Any],
    rng: random.Random,
) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for k, v in entry.items():
        if k.endswith("_pool"):
            short = k[: -len("_pool")]
            picked = _pick_from_pool(v, rng)
            if picked:
                out[short] = picked
    return out


def get_kongmang_slots(
    pillar: str,
    *,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    공망이 걸린 주(柱) 키(year/month/day/hour 또는 년주 등)를 받아 슬롯 문장을 반환한다.

    반환:
        found, pillar, label_ko, core_meaning 및
        life_theme / behavior / inner_state / relation / reframe 등.
    """
    pkey = _resolve_pillar(pillar)
    rng = random.Random(seed)
    patterns = _db().get("pillar_patterns", {})
    entry = patterns.get(pkey, {}) if pkey else {}
    if not entry:
        return {"found": False}

    pools = _pick_pool_fields(entry, rng)
    return {
        "found": True,
        "pillar": entry.get("pillar", pkey or ""),
        "label_ko": entry.get("label_ko", ""),
        "core_meaning": entry.get("core_meaning", ""),
        **pools,
    }
