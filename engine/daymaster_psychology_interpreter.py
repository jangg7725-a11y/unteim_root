# engine/daymaster_psychology_interpreter.py
# -*- coding: utf-8 -*-
"""
일간(천간) → 심리·행동 패턴 슬롯

narrative/daymaster_psychology_db.json 을 조회해 풀(slots)마다 랜덤 1문장을 선택한다.
"""

from __future__ import annotations

import random
from typing import Any, Dict, Optional

from utils.narrative_loader import load_sentences

_DB_FILE = "daymaster_psychology_db"


def _db() -> Dict[str, Any]:
    return load_sentences(_DB_FILE)


def _key_map() -> Dict[str, str]:
    return _db().get("engine_mapping", {}).get("key_map", {})


def _resolve_gan(gan: str) -> Optional[str]:
    name = str(gan).strip()
    if not name:
        return None
    kmap = _key_map()
    if name in kmap:
        return kmap[name]
    day = _db().get("daymaster", {})
    if name in day:
        return name
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


def get_daymaster_slots(
    gan: str,
    *,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    일간 문자열을 받아 DB 프로필에서 각 *_pool 에 대해 랜덤 1문장을 골라 반환한다.

    반환:
        found 가 False 이면 공통 메타만 없는 최소 dict.
        True 이면 gan, label, element, nature, core_image 및
        identity / behavior / inner_state / relation / stress / strength / reframe / monthly_advice 등.
    """
    key = _resolve_gan(gan)
    rng = random.Random(seed)
    day = _db().get("daymaster", {})
    entry = day.get(key, {}) if key else {}
    if not entry:
        return {"found": False}

    pools = _pick_pool_fields(entry, rng)
    return {
        "found": True,
        "gan": entry.get("gan", key or ""),
        "label": entry.get("label", ""),
        "element": entry.get("element", ""),
        "nature": entry.get("nature", ""),
        "core_image": entry.get("core_image", ""),
        **pools,
    }
