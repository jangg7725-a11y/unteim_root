# engine/monthly_action_guide_interpreter.py
# -*- coding: utf-8 -*-
"""
월별 실천 가이드 — narrative/monthly_action_guide_db.json 조회
"""

from __future__ import annotations

import random
from typing import Any, Dict, Optional

from utils.narrative_loader import load_sentences

_DB_FILE = "monthly_action_guide_db"

_FLOW_TO_POOL = {
    "rising": "rising_pool",
    "stable": "stable_pool",
    "caution": "caution_pool",
}

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


def _pick_from_pool(pool: Any, rng: random.Random) -> str:
    if isinstance(pool, str) and pool.strip():
        return pool
    if isinstance(pool, list) and pool:
        return str(rng.choice(pool))
    return ""


def _resolve_gan(gan: str) -> Optional[str]:
    raw = str(gan).strip()
    if not raw:
        return None
    tips = _db().get("daymaster_monthly_tip", {})
    if raw in tips and not raw.startswith("_"):
        return raw
    if raw in _GAN_ALIASES:
        key = _GAN_ALIASES[raw]
        if key in tips:
            return key
    return None


def get_oheng_guide(
    oheng_key: str,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    oheng_monthly_strategy[oheng_key] 의 strategy_pool / caution_pool / action_pool 에서
    각각 랜덤 1문장을 고른다.
    """
    key = str(oheng_key).strip()
    if not key or key.startswith("_"):
        return {"found": False}

    rng = random.Random(seed)
    entry = _db().get("oheng_monthly_strategy", {}).get(key)
    if not isinstance(entry, dict):
        return {"found": False}

    strategy = _pick_from_pool(entry.get("strategy_pool"), rng)
    caution = _pick_from_pool(entry.get("caution_pool"), rng)
    action = _pick_from_pool(entry.get("action_pool"), rng)

    if not (strategy or caution or action):
        return {"found": False}

    out: Dict[str, Any] = {
        "found": True,
        "oheng_key": key,
        "strategy": strategy,
        "caution": caution,
        "action": action,
    }
    if isinstance(entry.get("label"), str) and entry["label"].strip():
        out["label"] = entry["label"]
    if isinstance(entry.get("core"), str) and entry["core"].strip():
        out["core"] = entry["core"]
    return out


def get_topic_guide(
    topic_id: str,
    flow_type: str,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    topic_monthly_guide[topic_id] 에서 flow_type 에 해당하는 풀
    (rising→rising_pool, stable→stable_pool, caution→caution_pool) 에서 랜덤 1문장.
    """
    tid = str(topic_id).strip()
    ft = str(flow_type).strip()
    if not tid or tid.startswith("_"):
        return {"found": False}

    pool_key = _FLOW_TO_POOL.get(ft)
    if not pool_key:
        return {"found": False}

    rng = random.Random(seed)
    entry = _db().get("topic_monthly_guide", {}).get(tid)
    if not isinstance(entry, dict):
        return {"found": False}

    text = _pick_from_pool(entry.get(pool_key), rng)
    if not text:
        return {"found": False}

    out: Dict[str, Any] = {
        "found": True,
        "topic_id": tid,
        "flow_type": ft,
        "guide": text,
    }
    if isinstance(entry.get("label"), str) and entry["label"].strip():
        out["label"] = entry["label"]
    return out


def get_daymaster_tip(
    gan: str,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """daymaster_monthly_tip[gan] 의 monthly_tip_pool 에서 랜덤 1문장."""
    key = _resolve_gan(gan)
    if not key:
        return {"found": False}

    rng = random.Random(seed)
    entry = _db().get("daymaster_monthly_tip", {}).get(key)
    if not isinstance(entry, dict):
        return {"found": False}

    tip = _pick_from_pool(entry.get("monthly_tip_pool"), rng)
    if not tip:
        return {"found": False}

    out: Dict[str, Any] = {
        "found": True,
        "gan": key,
        "tip": tip,
    }
    if isinstance(entry.get("label"), str) and entry["label"].strip():
        out["label"] = entry["label"]
    return out


def get_week_guide(
    week_num: Any,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """week_rhythm_guide[\"week{N}\"] 의 guide_pool 에서 랜덤 1문장."""
    try:
        n = int(week_num)
    except (TypeError, ValueError):
        return {"found": False}
    if n < 1:
        return {"found": False}

    wkey = f"week{n}"
    rng = random.Random(seed)
    entry = _db().get("week_rhythm_guide", {}).get(wkey)
    if not isinstance(entry, dict):
        return {"found": False}

    guide = _pick_from_pool(entry.get("guide_pool"), rng)
    if not guide:
        return {"found": False}

    out: Dict[str, Any] = {
        "found": True,
        "week": n,
        "week_key": wkey,
        "guide": guide,
    }
    if isinstance(entry.get("label"), str) and entry["label"].strip():
        out["label"] = entry["label"]
    return out
