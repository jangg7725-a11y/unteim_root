# engine/geukguk_narrative_interpreter.py
# -*- coding: utf-8 -*-
"""
격국 → 인생 서사·심리 패턴 슬롯

narrative/geukguk_narrative_db.json 을 조회해 풀당 랜덤 1문장을 선택한다.
"""

from __future__ import annotations

import random
from typing import Any, Dict, Optional

from utils.narrative_loader import load_sentences

_DB_FILE = "geukguk_narrative_db"


def _db() -> Dict[str, Any]:
    return load_sentences(_DB_FILE)


def _key_map() -> Dict[str, str]:
    return _db().get("engine_mapping", {}).get("key_map", {})


def _resolve_geukguk(name: str) -> Optional[str]:
    raw = str(name).strip()
    if not raw:
        return None
    kmap = _key_map()
    if raw in kmap:
        return kmap[raw]
    gg = _db().get("geukguk", {})
    if raw in gg:
        return raw
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


def get_geukguk_slots(
    geukguk_name: str,
    *,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    격국 식별자(한글명 등)를 받아 각 *_pool 에서 랜덤 1문장 반환.

    반환:
        found, geukguk_id, label_ko, core_narrative 및
        life_theme / behavior / inner_state / relation / career / growth / reframe 등.
    """
    key = _resolve_geukguk(geukguk_name)
    rng = random.Random(seed)
    gg = _db().get("geukguk", {})
    entry = gg.get(key, {}) if key else {}
    if not entry:
        return {"found": False}

    pools = _pick_pool_fields(entry, rng)
    return {
        "found": True,
        "geukguk_id": entry.get("geukguk_id", key or ""),
        "label_ko": entry.get("label_ko", ""),
        "core_narrative": entry.get("core_narrative", ""),
        **pools,
    }
