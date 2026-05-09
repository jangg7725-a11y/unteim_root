# engine/healing_interpreter.py
# -*- coding: utf-8 -*-
"""
위로문 DB → 상담 GPT 프롬프트용 슬롯

narrative/healing_message_db.json 을 로드해
① 공감(comfort) · ③ 원인·통찰(insight) · ④ 제안(action) 풀에서 문장을 선택한다.
"""

from __future__ import annotations

import random
from typing import Any, Dict, Optional

from utils.narrative_loader import load_sentences

_DB_FILE = "healing_message_db"


def _db() -> Dict[str, Any]:
    return load_sentences(_DB_FILE)


def _situations() -> Dict[str, Any]:
    return _db().get("situations", {})


def _pick_pool(
    pool: Any,
    rng: random.Random,
) -> str:
    if isinstance(pool, str) and pool.strip():
        return pool.strip()
    if isinstance(pool, list) and pool:
        return str(rng.choice(pool)).strip()
    return ""


def get_healing_slots(
    situation_id: str,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    situation_id 에 해당하는 comfort / insight / action (integrated) 풀에서
    각각 랜덤 1문장을 고른다.

    Returns
    -------
    found 가 False 이면 최소 키만.
    True 이면 situation_id, label_ko, comfort, insight, action, integrated.
    """
    sid = str(situation_id).strip()
    rng = random.Random(seed)
    sit = _situations().get(sid) or {}
    if not sit:
        return {"found": False, "situation_id": sid}

    return {
        "found": True,
        "situation_id": sit.get("situation_id", sid),
        "label_ko": sit.get("label_ko", ""),
        "comfort": _pick_pool(sit.get("comfort_pool", []), rng),
        "insight": _pick_pool(sit.get("insight_pool", []), rng),
        "action": _pick_pool(sit.get("action_pool", []), rng),
        "integrated": _pick_pool(sit.get("integrated_pool", []), rng),
    }


def detect_situation(user_text: str) -> Optional[str]:
    """
    사용자 발화에 등장하는 trigger_keywords 개수가 가장 많은 상황을 선택한다.
    동점이면 DB 정의 순서(딕셔너리 삽입 순)가 앞선 상황을 택한다.
    """
    t = (user_text or "").strip()
    if not t:
        return None

    best_id: Optional[str] = None
    best_score = 0
    for sid, sit in _situations().items():
        kws = sit.get("trigger_keywords") or []
        score = 0
        for kw in kws:
            if isinstance(kw, str) and kw and kw in t:
                score += 1
        if score > best_score:
            best_score = score
            best_id = str(sid)

    if best_id and best_score > 0:
        return best_id
    return None


def format_healing_prompt_block(
    user_text: str,
    *,
    seed: Optional[int] = None,
) -> str:
    """
    상담 system 프롬프트에 붙일 블록.
    감지된 상황이 없거나 슬롯이 비면 빈 문자열.
    """
    sid = detect_situation(user_text)
    if not sid:
        return ""
    slots = get_healing_slots(sid, seed=seed)
    if not slots.get("found"):
        return ""

    label = slots.get("label_ko") or sid
    c = slots.get("comfort") or ""
    ins = slots.get("insight") or ""
    act = slots.get("action") or ""
    if not (c or ins or act):
        return ""

    return (
        "\n\n"
        "【힐링·감정 DB 참고 — ① 공감 / ③ 원인·통찰 / ④ 제안을 쓸 때 아래를 참고하되, "
        "문장을 그대로 읽지 말고 코칭 톤으로 재구성하세요】\n"
        f"· 상황 유형: {label}\n"
        f"· ① 공감 방향: {c}\n"
        f"· ③ 원인·통찰 방향: {ins}\n"
        f"· ④ 제안 방향: {act}\n"
    )
