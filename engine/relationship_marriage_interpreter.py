# engine/relationship_marriage_interpreter.py
# -*- coding: utf-8 -*-
"""
인연·연애·결혼 패턴 DB → GPT 프롬프트용 슬롯

narrative/relationship_marriage_db.json 을 로드해
① 오행별 관계·인연 성향
② 인연·연애 흐름별 슬롯
③ 결혼 준비·결정 케이스 슬롯
④ 관계 갈등·위기 케이스 슬롯
⑤ 궁합 흐름별 안내 슬롯
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from utils.narrative_loader import load_sentences

_DB_FILE = "relationship_marriage_db"


def _db() -> Dict[str, Any]:
    return load_sentences(_DB_FILE)


def _pick(pool: Any, rng: random.Random) -> str:
    if isinstance(pool, str) and pool.strip():
        return pool.strip()
    if isinstance(pool, list) and pool:
        return str(rng.choice(pool)).strip()
    return ""


def _resolve_oheng(oheng: str) -> Optional[str]:
    omap = _db().get("engine_mapping", {}).get("oheng_key_map", {})
    name = str(oheng).strip()
    return omap.get(name) or (name if name in _db().get("oheng_relation", {}) else None)


def detect_relation_intent(text: str) -> Optional[str]:
    """텍스트에서 관계 인텐트 감지."""
    imap = _db().get("engine_mapping", {}).get("intent_map", {})
    for kw, intent in imap.items():
        if kw in str(text):
            return intent
    return None


# ── 공개 API ──────────────────────────────────────────

def get_oheng_relation_slots(oheng: str, *, seed: Optional[int] = None) -> Dict[str, Any]:
    """오행으로 관계·인연 성향 슬롯 조회."""
    key = _resolve_oheng(oheng)
    rng = random.Random(seed)
    entry = _db().get("oheng_relation", {}).get(key) if key else None
    if not entry:
        return {"found": False, "oheng": oheng}
    return {
        "found": True,
        "oheng_id": key,
        "label_ko": entry.get("label_ko", ""),
        "trait": _pick(entry.get("trait_pool", []), rng),
        "strength": _pick(entry.get("strength_pool", []), rng),
        "weakness": _pick(entry.get("weakness_pool", []), rng),
        "advice": _pick(entry.get("advice_pool", []), rng),
    }


def get_love_flow_slots(flow: str, *, seed: Optional[int] = None) -> Dict[str, Any]:
    """
    인연·연애 흐름 슬롯 조회.
    flow: meeting / early_stage / stable / apart / no_meet
    """
    rng = random.Random(seed)
    entry = _db().get("love_flow", {}).get(flow)
    if not entry:
        return {"found": False, "flow": flow}
    return {
        "found": True,
        "flow_id": entry.get("flow_id", flow),
        "label_ko": entry.get("label_ko", ""),
        "sentence": _pick(entry.get("sentence_pool", []), rng),
    }


def get_marriage_slots(case: str, *, seed: Optional[int] = None) -> Dict[str, Any]:
    """
    결혼 케이스 슬롯 조회.
    case: considering / preparing / delayed
    """
    rng = random.Random(seed)
    entry = _db().get("marriage", {}).get(case)
    if not entry:
        return {"found": False, "case": case}
    return {
        "found": True,
        "case_id": entry.get("case_id", case),
        "label_ko": entry.get("label_ko", ""),
        "sentence": _pick(entry.get("sentence_pool", []), rng),
    }


def get_conflict_slots(case: str, *, seed: Optional[int] = None) -> Dict[str, Any]:
    """
    갈등 케이스 슬롯 조회.
    case: communication / trust / distance
    """
    rng = random.Random(seed)
    entry = _db().get("conflict", {}).get(case)
    if not entry:
        return {"found": False, "case": case}
    return {
        "found": True,
        "case_id": entry.get("case_id", case),
        "label_ko": entry.get("label_ko", ""),
        "sentence": _pick(entry.get("sentence_pool", []), rng),
    }


def get_compatibility_hint_slots(flow: str = "neutral_flow", *, seed: Optional[int] = None) -> Dict[str, Any]:
    """
    궁합 흐름 슬롯 조회.
    flow: good_flow / challenging_flow / neutral_flow
    """
    rng = random.Random(seed)
    entry = _db().get("compatibility_hint", {}).get(flow)
    if not entry:
        return {"found": False, "flow": flow}
    return {
        "found": True,
        "flow_id": entry.get("flow_id", flow),
        "label_ko": entry.get("label_ko", ""),
        "sentence": _pick(entry.get("sentence_pool", []), rng),
    }


def get_relation_context_for_packed(
    packed: Dict[str, Any], *, seed: Optional[int] = None
) -> Dict[str, Any]:
    """packed 사주에서 오행 자동 추출 후 슬롯 반환."""
    element: str = (
        packed.get("day_element")
        or packed.get("analysis", {}).get("day_master", {}).get("element", "")
    )
    oh = get_oheng_relation_slots(element, seed=seed) if element else {"found": False}
    return {"found": oh.get("found", False), "oheng": oh}


def format_relation_prompt_block(
    packed: Dict[str, Any],
    user_text: str = "",
    love_flow: str = "",
    compat_flow: str = "",
    *,
    seed: Optional[int] = None,
) -> str:
    """GPT 프롬프트 삽입용 인연·결혼 블록 문자열 반환."""
    lines: List[str] = []

    ctx = get_relation_context_for_packed(packed, seed=seed)
    oh = ctx.get("oheng", {})
    if oh.get("found"):
        lines.append(f"[관계 성향 — {oh.get('label_ko', '')}]")
        if oh.get("trait"):
            lines.append(oh["trait"])
        if oh.get("strength"):
            lines.append(f"강점: {oh['strength']}")
        if oh.get("advice"):
            lines.append(f"조언: {oh['advice']}")

    # 인연 흐름
    if love_flow:
        fl = get_love_flow_slots(love_flow, seed=seed)
        if fl.get("found"):
            lines.append(f"\n[{fl.get('label_ko', '')}]")
            lines.append(fl.get("sentence", ""))
    elif user_text:
        intent = detect_relation_intent(user_text)
        if intent == "marriage":
            m = get_marriage_slots("considering", seed=seed)
        elif intent == "conflict" or intent == "communication":
            m = get_conflict_slots("communication", seed=seed)
        elif intent == "apart":
            m = get_love_flow_slots("apart", seed=seed)
        elif intent == "meeting":
            m = get_love_flow_slots("meeting", seed=seed)
        else:
            m = {"found": False}
        if m.get("found"):
            lines.append(f"\n[{m.get('label_ko', '')}]")
            lines.append(m.get("sentence", ""))

    # 궁합 흐름
    if compat_flow:
        cp = get_compatibility_hint_slots(compat_flow, seed=seed)
        if cp.get("found"):
            lines.append(f"\n[궁합 — {cp.get('label_ko', '')}]")
            lines.append(cp.get("sentence", ""))

    return "\n".join(lines)
