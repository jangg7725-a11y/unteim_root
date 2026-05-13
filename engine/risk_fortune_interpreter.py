# engine/risk_fortune_interpreter.py
# -*- coding: utf-8 -*-
"""
위험·행운 패턴 DB → GPT 프롬프트용 슬롯

narrative/risk_fortune_db.json 을 로드해
① 관재수 — 경고·행동·회복 슬롯
② 사고수 — 경고·행동·신체 부위 슬롯
③ 손재수 — 경고·행동·회복 슬롯
④ 횡재수 — 기회·관리·주의 슬롯
텍스트에서 위험 유형 자동 감지 지원.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from utils.narrative_loader import load_sentences

_DB_FILE = "risk_fortune_db"

_RISK_SECTIONS = {
    "gwanjaesu": "관재수",
    "accident_su": "사고수",
    "ibyeolsu": "이별수",
    "sonjaesu": "손재수",
    "hwongjaesu": "횡재수",
    "guseolsu": "구설수",
    "ohae": "오해",
}


def _db() -> Dict[str, Any]:
    return load_sentences(_DB_FILE)


def _pick(pool: Any, rng: random.Random) -> str:
    if isinstance(pool, str) and pool.strip():
        return pool.strip()
    if isinstance(pool, list) and pool:
        return str(rng.choice(pool)).strip()
    return ""


def detect_risk_type(text: str) -> Optional[str]:
    """사용자 텍스트에서 위험 유형 감지. 없으면 None."""
    tmap = _db().get("engine_mapping", {}).get("risk_type_map", {})
    for keyword, rtype in tmap.items():
        if keyword in str(text):
            return rtype
    return None


def get_risk_slots(
    risk_type: str, *, seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    위험 유형(gwanjaesu/accident_su/sonjaesu/hwongjaesu)으로 슬롯 조회.
    한글 키워드도 engine_mapping으로 자동 변환.
    """
    rng = random.Random(seed)
    tmap = _db().get("engine_mapping", {}).get("risk_type_map", {})
    resolved = tmap.get(risk_type, risk_type)
    section = _db().get(resolved)
    if not section:
        return {"found": False, "risk_type": risk_type}

    overview = section.get("overview", {})
    result: Dict[str, Any] = {
        "found": True,
        "risk_type": resolved,
        "label_ko": overview.get("label_ko", ""),
        "core_message": overview.get("core_message", ""),
    }

    if resolved == "hwongjaesu":
        result["opportunity"] = _pick(section.get("opportunity_pool", []), rng)
        result["management"] = _pick(section.get("management_pool", []), rng)
        result["caution"] = _pick(section.get("caution_pool", []), rng)
    else:
        result["warning"] = _pick(section.get("warning_pool", []), rng)
        result["action"] = _pick(section.get("action_pool", []), rng)
        result["recovery"] = _pick(section.get("recovery_pool", []), rng)

    return result


def has_risk_type(risk_type: str) -> bool:
    """
    DB에 해당 위험 유형 섹션이 존재하는지 확인.
    신살 매핑 결과가 실제 데이터를 가지는지 검증할 때 사용.
    """
    tmap = _db().get("engine_mapping", {}).get("risk_type_map", {})
    resolved = tmap.get(risk_type, risk_type)
    return bool(_db().get(resolved))


def get_shinsal_risk_slots(
    shinsal_name: str, *, seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """신살 이름으로 연결된 위험 유형 슬롯 목록 반환."""
    smap = _db().get("engine_mapping", {}).get("shinsal_risk_map", {})
    risk_types = smap.get(shinsal_name, [])
    results = []
    for rt in risk_types:
        slots = get_risk_slots(rt, seed=seed)
        if slots.get("found"):
            results.append(slots)
    return results


def get_combined_risk_slots(*, seed: Optional[int] = None) -> Dict[str, Any]:
    """복합 위험 시기 슬롯 조회."""
    rng = random.Random(seed)
    section = _db().get("combined_risk", {}).get("high_risk_period", {})
    if not section:
        return {"found": False}
    return {
        "found": True,
        "label_ko": section.get("label_ko", "복합 위험 시기"),
        "sentence": _pick(section.get("sentence_pool", []), rng),
    }


def format_risk_prompt_block(
    user_text: str = "",
    shinsal_list: Optional[List[str]] = None,
    risk_types: Optional[List[str]] = None,
    *,
    seed: Optional[int] = None,
) -> str:
    """
    GPT 프롬프트 삽입용 위험·행운 블록 문자열 반환.

    우선순위:
    1. risk_types 직접 지정
    2. user_text 에서 자동 감지
    3. shinsal_list 에서 연결
    """
    lines: List[str] = []
    collected: List[str] = []

    if risk_types:
        collected = list(risk_types)
    elif user_text:
        detected = detect_risk_type(user_text)
        if detected:
            collected = [detected]

    if shinsal_list:
        smap = _db().get("engine_mapping", {}).get("shinsal_risk_map", {})
        for s in shinsal_list:
            for rt in smap.get(s, []):
                if rt not in collected:
                    collected.append(rt)

    for rt in collected:
        slots = get_risk_slots(rt, seed=seed)
        if not slots.get("found"):
            continue
        label = slots.get("label_ko", rt)
        lines.append(f"[{label}]")
        lines.append(slots.get("core_message", ""))

        if rt == "hwongjaesu":
            if slots.get("opportunity"):
                lines.append(f"기회: {slots['opportunity']}")
            if slots.get("management"):
                lines.append(f"관리: {slots['management']}")
        else:
            if slots.get("warning"):
                lines.append(f"주의: {slots['warning']}")
            if slots.get("action"):
                lines.append(f"행동: {slots['action']}")
        lines.append("")

    return "\n".join(lines).strip()
