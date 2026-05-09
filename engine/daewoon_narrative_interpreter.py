# engine/daewoon_narrative_interpreter.py
# -*- coding: utf-8 -*-
"""
대운·세운 흐름 → 서사 슬롯

narrative/daewoon_sewun_narrative_db.json 을 조회해 flow_type / 세운 오버레이 힌트를 반환한다.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple

from utils.narrative_loader import load_sentences

_DB_FILE = "daewoon_sewun_narrative_db"

_FLOW_POOL_KEYS: List[Tuple[str, str]] = [
    ("era", "era_pool"),
    ("energy", "energy_pool"),
    ("opportunity", "opportunity_pool"),
    ("caution", "caution_pool"),
    ("action", "action_pool"),
    ("reframe", "reframe_pool"),
]


def _db() -> Dict[str, Any]:
    return load_sentences(_DB_FILE)


def _pick_from_pool(pool: Any, rng: random.Random) -> str:
    if isinstance(pool, str) and pool.strip():
        return pool
    if isinstance(pool, list) and pool:
        return str(rng.choice(pool))
    return ""


def get_flow_slots(
    flow_type_id: str,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    flow_types[flow_type_id] 의 6개 풀에서 각각 랜덤 1문장을 고른다.

    슬롯: era, energy, opportunity, caution, action, reframe
    """
    fid = str(flow_type_id).strip()
    if not fid:
        return {"found": False}

    rng = random.Random(seed)
    entry = _db().get("flow_types", {}).get(fid)
    if not isinstance(entry, dict):
        return {"found": False}

    slots: Dict[str, str] = {}
    for short, pool_key in _FLOW_POOL_KEYS:
        picked = _pick_from_pool(entry.get(pool_key), rng)
        if picked:
            slots[short] = picked

    if not slots:
        return {"found": False}

    return {
        "found": True,
        "flow_type_id": entry.get("flow_type_id", fid),
        "label_ko": entry.get("label_ko", ""),
        "core_message": entry.get("core_message", ""),
        **slots,
    }


def get_sewun_overlay_slots(
    overlay_type: str,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    sewun_overlays[overlay_type] 의 hint_pool 에서 랜덤 1문장을 고른다.
    """
    oid = str(overlay_type).strip()
    if not oid or oid.startswith("_"):
        return {"found": False}

    rng = random.Random(seed)
    entry = _db().get("sewun_overlays", {}).get(oid)
    if not isinstance(entry, dict):
        return {"found": False}

    hint = _pick_from_pool(entry.get("hint_pool"), rng)
    if not hint:
        return {"found": False}

    return {
        "found": True,
        "overlay_type": oid,
        "label_ko": entry.get("label_ko", ""),
        "hint": hint,
    }
