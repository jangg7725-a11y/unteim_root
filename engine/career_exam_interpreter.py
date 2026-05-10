# engine/career_exam_interpreter.py
# -*- coding: utf-8 -*-
"""
취업·합격·시험 패턴 DB → GPT 프롬프트용 슬롯

narrative/career_exam_db.json 을 로드해
① 오행별 취업·시험 전략
② 시험 흐름별 슬롯 (준비중/임박/합격/불합격/재도전)
③ 취업 케이스별 슬롯 (서류/면접/대기/이직 등)
④ 면접 상황별 슬롯
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from utils.narrative_loader import load_sentences

_DB_FILE = "career_exam_db"


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
    return omap.get(name) or (name if name in _db().get("oheng_career", {}) else None)


def detect_career_intent(text: str) -> Optional[str]:
    """텍스트에서 취업/시험 인텐트 감지."""
    imap = _db().get("engine_mapping", {}).get("intent_map", {})
    for kw, intent in imap.items():
        if kw in str(text):
            return intent
    return None


# ── 공개 API ──────────────────────────────────────────

def get_oheng_career_slots(oheng: str, *, seed: Optional[int] = None) -> Dict[str, Any]:
    """오행으로 취업·시험 전략 슬롯 조회."""
    key = _resolve_oheng(oheng)
    rng = random.Random(seed)
    entry = _db().get("oheng_career", {}).get(key) if key else None
    if not entry:
        return {"found": False, "oheng": oheng}
    return {
        "found": True,
        "oheng_id": key,
        "label_ko": entry.get("label_ko", ""),
        "strength": _pick(entry.get("strength_pool", []), rng),
        "weakness": _pick(entry.get("weakness_pool", []), rng),
        "strategy": _pick(entry.get("strategy_pool", []), rng),
    }


def get_exam_flow_slots(flow: str, *, seed: Optional[int] = None) -> Dict[str, Any]:
    """
    시험 흐름 슬롯 조회.
    flow: preparation / exam_soon / pass / fail / retrying
    """
    rng = random.Random(seed)
    entry = _db().get("exam_flow", {}).get(flow)
    if not entry:
        return {"found": False, "flow": flow}
    return {
        "found": True,
        "flow_id": entry.get("flow_id", flow),
        "label_ko": entry.get("label_ko", ""),
        "sentence": _pick(entry.get("sentence_pool", []), rng),
    }


def get_job_search_slots(case: str, *, seed: Optional[int] = None) -> Dict[str, Any]:
    """
    취업 케이스 슬롯 조회.
    case: resume / networking / waiting / multiple_offers
    """
    rng = random.Random(seed)
    entry = _db().get("job_search", {}).get(case)
    if not entry:
        return {"found": False, "case": case}
    return {
        "found": True,
        "case_id": entry.get("case_id", case),
        "label_ko": entry.get("label_ko", ""),
        "sentence": _pick(entry.get("sentence_pool", []), rng),
    }


def get_interview_slots(case: str = "preparation", *, seed: Optional[int] = None) -> Dict[str, Any]:
    """
    면접 상황 슬롯 조회.
    case: preparation / during / group
    """
    rng = random.Random(seed)
    entry = _db().get("interview", {}).get(case)
    if not entry:
        return {"found": False, "case": case}
    return {
        "found": True,
        "case_id": entry.get("case_id", case),
        "label_ko": entry.get("label_ko", ""),
        "sentence": _pick(entry.get("sentence_pool", []), rng),
    }


def get_career_context_for_packed(
    packed: Dict[str, Any], *, seed: Optional[int] = None
) -> Dict[str, Any]:
    """packed 사주에서 오행 자동 추출 후 슬롯 반환."""
    element: str = (
        packed.get("day_element")
        or packed.get("analysis", {}).get("day_master", {}).get("element", "")
    )
    oh = get_oheng_career_slots(element, seed=seed) if element else {"found": False}
    return {"found": oh.get("found", False), "oheng": oh}


def format_career_prompt_block(
    packed: Dict[str, Any],
    user_text: str = "",
    exam_flow: str = "",
    *,
    seed: Optional[int] = None,
) -> str:
    """GPT 프롬프트 삽입용 취업·합격 블록 문자열 반환."""
    lines: List[str] = []

    ctx = get_career_context_for_packed(packed, seed=seed)
    oh = ctx.get("oheng", {})
    if oh.get("found"):
        lines.append(f"[취업·시험 성향 — {oh.get('label_ko', '')}]")
        if oh.get("strength"):
            lines.append(f"강점: {oh['strength']}")
        if oh.get("strategy"):
            lines.append(f"전략: {oh['strategy']}")

    if exam_flow:
        flow = get_exam_flow_slots(exam_flow, seed=seed)
        if flow.get("found"):
            lines.append(f"\n[{flow.get('label_ko', '')}]")
            if flow.get("sentence"):
                lines.append(flow["sentence"])
    elif user_text:
        intent = detect_career_intent(user_text)
        if intent == "interview":
            iv = get_interview_slots("preparation", seed=seed)
            if iv.get("found"):
                lines.append(f"\n[{iv.get('label_ko', '')}]")
                lines.append(iv.get("sentence", ""))
        elif intent == "exam_flow":
            fl = get_exam_flow_slots("preparation", seed=seed)
            if fl.get("found"):
                lines.append(f"\n[{fl.get('label_ko', '')}]")
                lines.append(fl.get("sentence", ""))

    return "\n".join(lines)
