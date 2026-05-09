# engine/vocation_narrative_interpreter.py
# -*- coding: utf-8 -*-
"""
직업·진로 서사 슬롯

narrative/vocation_narrative_db.json 을 조회해 직업군별 풀·일간 힌트를 반환한다.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple

from utils.narrative_loader import load_sentences

_DB_FILE = "vocation_narrative_db"

_VOCATION_POOL_KEYS: List[Tuple[str, str]] = [
    ("identity", "identity_pool"),
    ("environment", "environment_pool"),
    ("strength", "strength_pool"),
    ("challenge", "challenge_pool"),
    ("growth", "growth_pool"),
    ("action", "action_pool"),
]

_GAN_ALIASES: Dict[str, str] = {
    "갑": "甲",
    "을": "乙",
    "병": "丙",
    "정": "丁",
    "무": "戊",
    "기": "己",
    "경": "庚",
    "신": "辛",
    "임": "壬",
    "계": "癸",
}


def _db() -> Dict[str, Any]:
    return load_sentences(_DB_FILE)


def _resolve_gan(gan: str) -> Optional[str]:
    raw = str(gan).strip()
    if not raw:
        return None
    hints = _db().get("daymaster_vocation_hint", {})
    if raw in hints and not str(raw).startswith("_"):
        return raw
    if raw in _GAN_ALIASES:
        key = _GAN_ALIASES[raw]
        if key in hints:
            return key
    return None


def _pick_from_pool(pool: Any, rng: random.Random) -> str:
    if isinstance(pool, str) and pool.strip():
        return pool
    if isinstance(pool, list) and pool:
        return str(rng.choice(pool))
    return ""


def get_vocation_slots(
    category_id: str,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    categories[category_id] 의 6개 풀에서 각각 랜덤 1문장을 고른다.

    슬롯: identity, environment, strength, challenge, growth, action
    """
    cid = str(category_id).strip()
    if not cid:
        return {"found": False}

    rng = random.Random(seed)
    entry = _db().get("categories", {}).get(cid)
    if not isinstance(entry, dict):
        return {"found": False}

    slots: Dict[str, str] = {}
    for short, pool_key in _VOCATION_POOL_KEYS:
        picked = _pick_from_pool(entry.get(pool_key), rng)
        if picked:
            slots[short] = picked

    if not slots:
        return {"found": False}

    return {
        "found": True,
        "category_id": entry.get("category_id", cid),
        "label_ko": entry.get("label_ko", ""),
        "core_fit": entry.get("core_fit", ""),
        **slots,
    }


def get_daymaster_vocation_hint(gan: str) -> Dict[str, Any]:
    """
    daymaster_vocation_hint[gan] 의 primary 리스트와 hint 를 반환한다.
    """
    key = _resolve_gan(gan)
    if not key:
        return {"found": False}

    hints = _db().get("daymaster_vocation_hint", {})
    entry = hints.get(key)
    if not isinstance(entry, dict):
        return {"found": False}

    primary = entry.get("primary")
    if not isinstance(primary, list):
        primary = []
    primary = [str(x) for x in primary if x is not None and str(x).strip()]

    hint = entry.get("hint", "")
    if not isinstance(hint, str):
        hint = str(hint) if hint is not None else ""

    if not primary and not (hint and hint.strip()):
        return {"found": False}

    return {
        "found": True,
        "gan": key,
        "primary": primary,
        "hint": hint,
    }
