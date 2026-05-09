# engine/health_pattern_interpreter.py
# -*- coding: utf-8 -*-
"""
건강 패턴 DB → 상담·리포트 GPT 프롬프트용 슬롯

narrative/health_pattern_db.json 을 로드해
① 오행별 건강 취약점·관리법
② 일간별 건강 성향
③ 심리-신체 연결 패턴
슬롯에서 랜덤 1문장을 선택한다.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from utils.narrative_loader import load_sentences

_DB_FILE = "health_pattern_db"


def _db() -> Dict[str, Any]:
    return load_sentences(_DB_FILE)


def _oheng_health() -> Dict[str, Any]:
    return _db().get("oheng_health", {})


def _daymaster_health() -> Dict[str, Any]:
    return _db().get("daymaster_health", {})


def _stress_body_map() -> Dict[str, Any]:
    return _db().get("stress_body_map", {})


def _season_health_hint() -> Dict[str, Any]:
    return _db().get("season_health_hint", {})


def _key_map() -> Dict[str, str]:
    return _db().get("engine_mapping", {}).get("key_map", {})


def _oheng_key_map() -> Dict[str, str]:
    return _db().get("engine_mapping", {}).get("oheng_key_map", {})


def _stress_trigger_map() -> Dict[str, str]:
    return _db().get("engine_mapping", {}).get("stress_trigger_map", {})


def _pick(pool: Any, rng: random.Random) -> str:
    if isinstance(pool, str) and pool.strip():
        return pool.strip()
    if isinstance(pool, list) and pool:
        return str(rng.choice(pool)).strip()
    return ""


def _resolve_gan(gan: str) -> Optional[str]:
    name = str(gan).strip()
    if not name:
        return None
    kmap = _key_map()
    if name in kmap:
        return kmap[name]
    dh = _daymaster_health()
    if name in dh:
        return name
    return None


def _resolve_oheng(oheng: str) -> Optional[str]:
    name = str(oheng).strip()
    if not name:
        return None
    omap = _oheng_key_map()
    if name in omap:
        return omap[name]
    oh = _oheng_health()
    if name in oh:
        return name
    return None


# ──────────────────────────────────────────────────
# 공개 API
# ──────────────────────────────────────────────────

def get_oheng_health_slots(
    oheng: str,
    *,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    오행(목/화/토/금/수 또는 木/火/土/金/水)으로 건강 패턴 슬롯 조회.

    Returns
    -------
    found=True 이면:
        oheng_id, label_ko, organ_system, core_theme,
        vulnerability, strength, care, monthly_hint
    """
    key = _resolve_oheng(oheng)
    rng = random.Random(seed)
    oh = _oheng_health()
    entry = oh.get(key) if key else None
    if not entry:
        return {"found": False, "oheng": oheng}

    return {
        "found": True,
        "oheng_id": entry.get("oheng_id", key),
        "label_ko": entry.get("label_ko", ""),
        "organ_system": entry.get("organ_system", ""),
        "core_theme": entry.get("core_theme", ""),
        "vulnerability": _pick(entry.get("vulnerability_pool", []), rng),
        "strength": _pick(entry.get("strength_pool", []), rng),
        "care": _pick(entry.get("care_pool", []), rng),
        "monthly_hint": _pick(entry.get("monthly_hint_pool", []), rng),
    }


def get_daymaster_health_slots(
    gan: str,
    *,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    일간(天干)으로 건강 성향 슬롯 조회.

    Returns
    -------
    found=True 이면:
        gan, label_ko, element, health_tendency, care_tip
    """
    key = _resolve_gan(gan)
    rng = random.Random(seed)
    dh = _daymaster_health()
    entry = dh.get(key) if key else None
    if not entry:
        return {"found": False, "gan": gan}

    return {
        "found": True,
        "gan": entry.get("gan", key),
        "label_ko": entry.get("label_ko", ""),
        "element": entry.get("element", ""),
        "health_tendency": _pick(entry.get("health_tendency_pool", []), rng),
        "care_tip": _pick(entry.get("care_tip_pool", []), rng),
    }


def get_stress_body_slots(
    stress_id: str,
    *,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    심리 상태 ID (anxiety/burnout/sadness/anger/fear)로
    신체 반응 패턴과 즉각 완화법 슬롯 조회.

    Returns
    -------
    found=True 이면:
        stress_id, label_ko, body_signal, relief
    """
    sid = str(stress_id).strip()
    rng = random.Random(seed)
    sbm = _stress_body_map()
    entry = sbm.get(sid) or {}
    if not entry:
        return {"found": False, "stress_id": sid}

    return {
        "found": True,
        "stress_id": entry.get("stress_id", sid),
        "label_ko": entry.get("label_ko", ""),
        "body_signal": _pick(entry.get("body_signal_pool", []), rng),
        "relief": _pick(entry.get("relief_pool", []), rng),
    }


def detect_stress_from_text(text: str) -> Optional[str]:
    """
    사용자 텍스트에서 심리-신체 연결 stress_id 를 탐지.
    매칭 없으면 None 반환.
    """
    text_lower = str(text).strip()
    tmap = _stress_trigger_map()
    for keyword, sid in tmap.items():
        if keyword in text_lower:
            return sid
    return None


def get_season_health_slots(
    season: str,
    *,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    계절(봄/여름/환절기/겨울)로 건강 힌트 슬롯 조회.
    """
    sname = str(season).strip()
    rng = random.Random(seed)
    sh = _season_health_hint()
    entry = sh.get(sname) or {}
    if not entry:
        return {"found": False, "season": sname}

    return {
        "found": True,
        "season": entry.get("season", sname),
        "organ_focus": entry.get("organ_focus", ""),
        "hint": _pick(entry.get("hint_pool", []), rng),
    }


def get_health_context_for_packed(
    packed: Dict[str, Any],
    *,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    packed 사주 데이터에서 일간·오행을 자동으로 추출해
    건강 패턴 슬롯을 한 번에 반환.

    packed 에서 탐색하는 키:
        day_gan / analysis.day_master.gan
        day_element / analysis.day_master.element
    """
    rng = random.Random(seed)

    # 일간 추출
    gan: str = (
        packed.get("day_gan")
        or packed.get("analysis", {}).get("day_master", {}).get("gan", "")
    )

    # 오행 추출 (일간 DB에서도 가져올 수 있음)
    element: str = (
        packed.get("day_element")
        or packed.get("analysis", {}).get("day_master", {}).get("element", "")
    )

    result: Dict[str, Any] = {"found": False}

    daymaster_slots = get_daymaster_health_slots(gan, seed=seed) if gan else {"found": False}
    oheng_slots = get_oheng_health_slots(element, seed=seed) if element else {"found": False}

    # 일간 DB에서 오행 보정
    if not oheng_slots.get("found") and daymaster_slots.get("found"):
        element = daymaster_slots.get("element", "")
        oheng_slots = get_oheng_health_slots(element, seed=seed) if element else {"found": False}

    if daymaster_slots.get("found") or oheng_slots.get("found"):
        result["found"] = True
        result["daymaster"] = daymaster_slots
        result["oheng"] = oheng_slots

    return result


def format_health_prompt_block(
    packed: Dict[str, Any],
    user_text: str = "",
    *,
    seed: Optional[int] = None,
) -> str:
    """
    GPT 프롬프트에 삽입할 건강 패턴 블록 문자열 반환.

    포함 내용:
    - 일간 건강 성향
    - 오행 건강 취약점 + 관리법
    - 심리-신체 연결 (user_text 에서 감지된 경우)
    """
    lines: List[str] = []

    ctx = get_health_context_for_packed(packed, seed=seed)

    if ctx.get("found"):
        dm = ctx.get("daymaster", {})
        if dm.get("found"):
            lines.append(f"[건강 성향 — {dm.get('label_ko', '')}]")
            if dm.get("health_tendency"):
                lines.append(dm["health_tendency"])
            if dm.get("care_tip"):
                lines.append(f"→ {dm['care_tip']}")

        oh = ctx.get("oheng", {})
        if oh.get("found"):
            lines.append(f"\n[{oh.get('label_ko', '')} 건강 패턴]")
            if oh.get("core_theme"):
                lines.append(oh["core_theme"])
            if oh.get("vulnerability"):
                lines.append(f"취약점: {oh['vulnerability']}")
            if oh.get("care"):
                lines.append(f"관리법: {oh['care']}")
            if oh.get("monthly_hint"):
                lines.append(f"이달 힌트: {oh['monthly_hint']}")

    if user_text:
        sid = detect_stress_from_text(user_text)
        if sid:
            stress_slots = get_stress_body_slots(sid, seed=seed)
            if stress_slots.get("found"):
                lines.append(f"\n[심리-신체 연결 — {stress_slots.get('label_ko', '')}]")
                if stress_slots.get("body_signal"):
                    lines.append(f"신체 반응: {stress_slots['body_signal']}")
                if stress_slots.get("relief"):
                    lines.append(f"즉각 완화: {stress_slots['relief']}")

    return "\n".join(lines)
