# engine/separation_movement_interpreter.py
# -*- coding: utf-8 -*-
"""
이별수(離別數)·이동수(移動數) 패턴 DB → 리포트·상담 슬롯

narrative/separation_movement_db.json 을 로드해
① 신살(역마살/화개살/고란살/도화살/지살/천살) 기반 탐지
② 십신(상관/편관/편인/비겁) 분포 기반 신호
③ 오행 과다/부족 기반 신호
④ 대운·세운 팔자 정보 기반 신호

사용법:
    from engine.separation_movement_interpreter import (
        get_separation_slots, get_movement_slots,
        get_sep_mov_context_for_packed,
    )
    slots = get_sep_mov_context_for_packed(packed, seed=42)
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Set

from utils.narrative_loader import load_sentences

_DB_FILE = "separation_movement_db"

# ── 신살 트리거 세트 ──────────────────────────────────────────────
_IBYEOL_SHINSAL: Set[str] = {"화개살", "고란살", "역마살", "도화", "도화살", "탕화살"}
_IDONG_SHINSAL: Set[str] = {"역마살", "지살", "천살", "반안살", "장성살"}

# ── 십신 트리거 ───────────────────────────────────────────────────
_IBYEOL_SIPSIN: Set[str] = {"상관", "편관", "비겁", "겁재"}
_IDONG_SIPSIN: Set[str] = {"편관", "상관", "편인"}

# ── 오행 키 정규화 (한자·한글 혼용 대응) ─────────────────────────
_OHENG_KO = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}


def _db() -> Dict[str, Any]:
    return load_sentences(_DB_FILE)


def _pick(pool: Any, rng: random.Random) -> str:
    if isinstance(pool, str) and pool.strip():
        return pool.strip()
    if isinstance(pool, list) and pool:
        return str(rng.choice(pool)).strip()
    return ""


# ── 내부 헬퍼 ────────────────────────────────────────────────────

def _get_shinsal_names(packed: Dict[str, Any]) -> List[str]:
    """packed 에서 실제 신살 이름 목록을 추출 (12운성 제외)."""
    items = (
        (packed.get("shinsal") or {}).get("items", [])
        if isinstance(packed.get("shinsal"), dict)
        else []
    )
    return [
        str(it.get("name") or "").strip()
        for it in items
        if isinstance(it, dict)
        and str(it.get("name") or "").strip()
        and not str(it.get("name") or "").startswith("12운성:")
    ]


def _get_oheng_counts(packed: Dict[str, Any]) -> Dict[str, int]:
    """오행 카운트 dict 반환. 키를 한글(목화토금수)로 정규화."""
    raw: Dict[str, Any] = (
        (packed.get("oheng") or {}).get("counts", {})
        or (packed.get("analysis") or {}).get("five_elements", {}).get("counts", {})
        or {}
    )
    result: Dict[str, int] = {}
    for k, v in raw.items():
        ko = _OHENG_KO.get(str(k), str(k))
        result[ko] = int(v) if isinstance(v, (int, float)) else 0
    return result


def _get_sipsin_counts(packed: Dict[str, Any]) -> Dict[str, int]:
    """
    십신 분포 카운트 dict 반환.
    packed 에서 가능한 위치:
      packed['sipsin_count'], packed['analysis']['sipsin_count'],
      packed['analysis']['sipsin_profile']
    """
    for path in (
        lambda p: p.get("sipsin_count"),
        lambda p: (p.get("analysis") or {}).get("sipsin_count"),
        lambda p: (p.get("analysis") or {}).get("sipsin_profile"),
    ):
        raw = path(packed)
        if isinstance(raw, dict) and raw:
            return {str(k): int(v) if isinstance(v, (int, float)) else 0 for k, v in raw.items()}
    return {}


def _get_daewoon_ten_god(packed: Dict[str, Any]) -> str:
    """현재 대운의 십신(천간 기준)을 추출. 없으면 ''."""
    daewoon = packed.get("daewoon") or []
    if not isinstance(daewoon, list):
        return ""
    for dw in daewoon:
        if isinstance(dw, dict) and dw.get("is_current"):
            return str(dw.get("stem_ten_god") or dw.get("ten_god") or "").strip()
    # is_current 없으면 첫 번째 사용
    if daewoon and isinstance(daewoon[0], dict):
        return str(daewoon[0].get("stem_ten_god") or daewoon[0].get("ten_god") or "").strip()
    return ""


def _detect_ibyeol_signals(
    shinsal_names: List[str],
    sipsin_counts: Dict[str, int],
    oheng_counts: Dict[str, int],
    daewoon_tg: str,
) -> List[str]:
    """이별수 신호 목록 반환."""
    signals: List[str] = []
    total_oheng = sum(oheng_counts.values()) or 1

    # 1) 신살 기반
    for s in shinsal_names:
        if s in _IBYEOL_SHINSAL:
            signals.append(f"shinsal:{s}")

    # 2) 십신 기반 (2개 이상 = 과다)
    for sipsin, threshold in (("상관", 2), ("편관", 2), ("비겁", 2), ("겁재", 2)):
        if sipsin_counts.get(sipsin, 0) >= threshold:
            signals.append(f"sipsin:{sipsin}")

    # 3) 오행 기반 — 금(金) 45% 이상 or 수(水) 40% 이상
    if oheng_counts.get("금", 0) / total_oheng >= 0.45:
        signals.append("oheng:금강")
    if oheng_counts.get("수", 0) / total_oheng >= 0.40:
        signals.append("oheng:수강")
    if oheng_counts.get("목", 0) / total_oheng < 0.10 and total_oheng >= 4:
        signals.append("oheng:목약")

    # 4) 대운 십신 기반
    if daewoon_tg in ("상관", "편관", "겁재"):
        signals.append(f"daewoon:{daewoon_tg}")

    return signals


def _detect_idong_signals(
    shinsal_names: List[str],
    sipsin_counts: Dict[str, int],
    oheng_counts: Dict[str, int],
    daewoon_tg: str,
) -> List[str]:
    """이동수 신호 목록 반환."""
    signals: List[str] = []
    total_oheng = sum(oheng_counts.values()) or 1

    # 1) 신살 기반
    for s in shinsal_names:
        if s in _IDONG_SHINSAL:
            signals.append(f"shinsal:{s}")

    # 2) 십신 기반
    for sipsin, threshold in (("편관", 2), ("상관", 2), ("편인", 2)):
        if sipsin_counts.get(sipsin, 0) >= threshold:
            signals.append(f"sipsin:{sipsin}")

    # 3) 오행 기반 — 목(木)/화(火) 35% 이상 or 금(金) 45% 이상(결단)
    if oheng_counts.get("목", 0) / total_oheng >= 0.35:
        signals.append("oheng:목강")
    if oheng_counts.get("화", 0) / total_oheng >= 0.35:
        signals.append("oheng:화강")
    if oheng_counts.get("금", 0) / total_oheng >= 0.45:
        signals.append("oheng:금강")

    # 4) 대운 십신 기반
    if daewoon_tg in ("편관", "상관", "편인"):
        signals.append(f"daewoon:{daewoon_tg}")

    return signals


# ── 공개 API ─────────────────────────────────────────────────────

def get_separation_slots(
    packed: Dict[str, Any],
    *,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    이별수 슬롯 반환.
    found=True 이면 trigger_signals, core_message, warning, action, recovery, context 포함.
    """
    rng = random.Random(seed)
    db = _db()
    section = db.get("ibyeol_su", {})
    if not section:
        return {"found": False}

    shinsal_names = _get_shinsal_names(packed)
    sipsin_counts = _get_sipsin_counts(packed)
    oheng_counts = _get_oheng_counts(packed)
    daewoon_tg = _get_daewoon_ten_god(packed)

    signals = _detect_ibyeol_signals(shinsal_names, sipsin_counts, oheng_counts, daewoon_tg)
    if not signals:
        return {"found": False}

    # 신살 컨텍스트 선택 (첫 번째 신살 기반)
    shinsal_ctx_map = section.get("shinsal_context", {})
    sipsin_ctx_map = section.get("sipsin_context", {})
    oheng_ctx_map = section.get("oheng_context", {})

    context_parts: List[str] = []
    for sig in signals[:2]:
        kind, val = sig.split(":", 1)
        if kind == "shinsal" and val in shinsal_ctx_map:
            context_parts.append(shinsal_ctx_map[val])
        elif kind == "sipsin" and val in sipsin_ctx_map:
            context_parts.append(sipsin_ctx_map[val])
        elif kind == "oheng" and val in oheng_ctx_map:
            context_parts.append(oheng_ctx_map[val])
        elif kind == "daewoon":
            context_parts.append(f"{val} 흐름에서 관계 변화 에너지가 강해지는 시기입니다.")

    overview = section.get("overview", {})
    return {
        "found": True,
        "type": "ibyeol_su",
        "label_ko": overview.get("label_ko", "이별수(離別數)"),
        "core_message": overview.get("core_message", ""),
        "warning": _pick(section.get("warning_pool", []), rng),
        "action": _pick(section.get("action_pool", []), rng),
        "recovery": _pick(section.get("recovery_pool", []), rng),
        "context": " ".join(context_parts[:1]),
        "trigger_signals": signals[:3],
    }


def get_movement_slots(
    packed: Dict[str, Any],
    *,
    seed: Optional[int] = None,
    movement_type: str = "general",
) -> Dict[str, Any]:
    """
    이동수 슬롯 반환.
    movement_type: 'general' | 'ijik' | 'isa' | 'transfer'
    found=True 이면 trigger_signals, core_message, guidance, action, caution, context 포함.
    """
    rng = random.Random(seed)
    db = _db()
    section = db.get("idong_su", {})
    if not section:
        return {"found": False}

    shinsal_names = _get_shinsal_names(packed)
    sipsin_counts = _get_sipsin_counts(packed)
    oheng_counts = _get_oheng_counts(packed)
    daewoon_tg = _get_daewoon_ten_god(packed)

    signals = _detect_idong_signals(shinsal_names, sipsin_counts, oheng_counts, daewoon_tg)
    if not signals:
        return {"found": False}

    # 이동 유형별 풀 선택
    pool_map = {
        "ijik": "ijik_pool",
        "isa": "isa_pool",
        "transfer": "transfer_pool",
        "general": "general_guidance_pool",
    }
    pool_key = pool_map.get(movement_type, "general_guidance_pool")
    guidance_pool = section.get(pool_key) or section.get("general_guidance_pool", [])

    # 컨텍스트 구성
    shinsal_ctx_map = section.get("shinsal_context", {})
    sipsin_ctx_map = section.get("sipsin_context", {})
    oheng_ctx_map = section.get("oheng_context", {})
    daewoon_ctx_map = section.get("daewoon_context", {})

    context_parts: List[str] = []
    for sig in signals[:2]:
        kind, val = sig.split(":", 1)
        if kind == "shinsal" and val in shinsal_ctx_map:
            context_parts.append(shinsal_ctx_map[val])
        elif kind == "sipsin" and val in sipsin_ctx_map:
            context_parts.append(sipsin_ctx_map[val])
        elif kind == "oheng" and val in oheng_ctx_map:
            context_parts.append(oheng_ctx_map[val])
        elif kind == "daewoon":
            key = f"{val}대운"
            if key in daewoon_ctx_map:
                context_parts.append(daewoon_ctx_map[key])

    overview = section.get("overview", {})
    return {
        "found": True,
        "type": "idong_su",
        "label_ko": overview.get("label_ko", "이동수(移動數)"),
        "core_message": overview.get("core_message", ""),
        "guidance": _pick(guidance_pool, rng),
        "action": _pick(section.get("caution_pool", []), rng),
        "context": " ".join(context_parts[:1]),
        "trigger_signals": signals[:3],
    }


def get_sep_mov_context_for_packed(
    packed: Dict[str, Any],
    *,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    packed 사주 데이터에서 이별수·이동수를 자동 감지해 슬롯 반환.

    Returns:
        {
            "separation": { found, label_ko, core_message, warning, action, context, trigger_signals },
            "movement":   { found, label_ko, core_message, guidance, action, context, trigger_signals },
        }
    """
    separation = get_separation_slots(packed, seed=seed)
    movement = get_movement_slots(packed, seed=seed)
    return {
        "separation": separation,
        "movement": movement,
    }


def format_sep_mov_prompt_block(
    packed: Dict[str, Any],
    *,
    seed: Optional[int] = None,
) -> str:
    """GPT 프롬프트 삽입용 이별수·이동수 블록 문자열 반환."""
    lines: List[str] = []
    ctx = get_sep_mov_context_for_packed(packed, seed=seed)

    sep = ctx.get("separation", {})
    if sep.get("found"):
        lines.append(f"[{sep.get('label_ko', '이별수')}]")
        if sep.get("context"):
            lines.append(sep["context"])
        if sep.get("warning"):
            lines.append(f"주의: {sep['warning']}")
        if sep.get("action"):
            lines.append(f"행동: {sep['action']}")
        lines.append("")

    mov = ctx.get("movement", {})
    if mov.get("found"):
        lines.append(f"[{mov.get('label_ko', '이동수')}]")
        if mov.get("context"):
            lines.append(mov["context"])
        if mov.get("guidance"):
            lines.append(f"안내: {mov['guidance']}")
        if mov.get("action"):
            lines.append(f"주의: {mov['action']}")
        lines.append("")

    return "\n".join(lines).strip()
