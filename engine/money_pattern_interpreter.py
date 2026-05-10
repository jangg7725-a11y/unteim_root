# engine/money_pattern_interpreter.py
# -*- coding: utf-8 -*-
"""
재물 패턴 DB → GPT 프롬프트용 슬롯

narrative/money_pattern_db.json 을 로드해
① 오행별 금전 성향
② 일간별 금전 특성
③ 재물 흐름 케이스 (안정/상승/손재/횡재)
④ 지출 패턴 / 투자 성향
슬롯에서 랜덤 1문장을 선택한다.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from utils.narrative_loader import load_sentences

_DB_FILE = "money_pattern_db"


def _db() -> Dict[str, Any]:
    return load_sentences(_DB_FILE)


def _pick(pool: Any, rng: random.Random) -> str:
    if isinstance(pool, str) and pool.strip():
        return pool.strip()
    if isinstance(pool, list) and pool:
        return str(rng.choice(pool)).strip()
    return ""


def _resolve_oheng(oheng: str) -> Optional[str]:
    name = str(oheng).strip()
    omap = _db().get("engine_mapping", {}).get("oheng_key_map", {})
    if name in omap:
        return omap[name]
    if name in _db().get("oheng_money", {}):
        return name
    return None


def _resolve_gan(gan: str) -> Optional[str]:
    name = str(gan).strip()
    kmap = _db().get("engine_mapping", {}).get("key_map", {})
    if name in kmap:
        return kmap[name]
    if name in _db().get("daymaster_money", {}):
        return name
    return None


# ── 공개 API ──────────────────────────────────────────

def get_oheng_money_slots(oheng: str, *, seed: Optional[int] = None) -> Dict[str, Any]:
    """오행으로 재물 성향 슬롯 조회."""
    key = _resolve_oheng(oheng)
    rng = random.Random(seed)
    entry = _db().get("oheng_money", {}).get(key) if key else None
    if not entry:
        return {"found": False, "oheng": oheng}
    return {
        "found": True,
        "oheng_id": entry.get("oheng_id", key),
        "label_ko": entry.get("label_ko", ""),
        "core_theme": entry.get("core_theme", ""),
        "strength": _pick(entry.get("strength_pool", []), rng),
        "weakness": _pick(entry.get("weakness_pool", []), rng),
        "advice": _pick(entry.get("advice_pool", []), rng),
        "monthly": _pick(entry.get("monthly_pool", []), rng),
    }


def get_daymaster_money_slots(gan: str, *, seed: Optional[int] = None) -> Dict[str, Any]:
    """일간으로 금전 특성 슬롯 조회."""
    key = _resolve_gan(gan)
    rng = random.Random(seed)
    entry = _db().get("daymaster_money", {}).get(key) if key else None
    if not entry:
        return {"found": False, "gan": gan}
    return {
        "found": True,
        "gan": entry.get("gan", key),
        "label_ko": entry.get("label_ko", ""),
        "element": entry.get("element", ""),
        "money_trait": _pick(entry.get("money_trait_pool", []), rng),
        "caution": _pick(entry.get("caution_pool", []), rng),
    }


def get_money_flow_slots(flow_type: str, *, seed: Optional[int] = None) -> Dict[str, Any]:
    """재물 흐름 케이스 슬롯 조회. flow_type: stable/growing/declining/windfall/loss"""
    rng = random.Random(seed)
    # 키워드 → flow_type 매핑
    tmap = _db().get("engine_mapping", {}).get("flow_trigger_map", {})
    resolved = tmap.get(flow_type, flow_type)
    entry = _db().get("money_flow_cases", {}).get(resolved)
    if not entry:
        return {"found": False, "flow_type": flow_type}
    return {
        "found": True,
        "case_id": entry.get("case_id", resolved),
        "label_ko": entry.get("label_ko", ""),
        "sentence": _pick(entry.get("sentence_pool", []), rng),
    }


def get_money_context_for_packed(
    packed: Dict[str, Any], *, seed: Optional[int] = None
) -> Dict[str, Any]:
    """packed 사주에서 일간·오행 자동 추출 후 슬롯 반환."""
    gan: str = (
        packed.get("day_gan")
        or packed.get("analysis", {}).get("day_master", {}).get("gan", "")
    )
    element: str = (
        packed.get("day_element")
        or packed.get("analysis", {}).get("day_master", {}).get("element", "")
    )
    dm = get_daymaster_money_slots(gan, seed=seed) if gan else {"found": False}
    oh = get_oheng_money_slots(element, seed=seed) if element else {"found": False}
    if not oh.get("found") and dm.get("found"):
        oh = get_oheng_money_slots(dm.get("element", ""), seed=seed)
    found = dm.get("found") or oh.get("found")
    return {"found": found, "daymaster": dm, "oheng": oh}


def format_money_prompt_block(
    packed: Dict[str, Any],
    flow_type: str = "",
    *,
    seed: Optional[int] = None,
) -> str:
    """GPT 프롬프트 삽입용 재물 블록 문자열 반환."""
    lines: List[str] = []
    ctx = get_money_context_for_packed(packed, seed=seed)

    dm = ctx.get("daymaster", {})
    if dm.get("found"):
        lines.append(f"[재물 성향 — {dm.get('label_ko', '')}]")
        if dm.get("money_trait"):
            lines.append(dm["money_trait"])
        if dm.get("caution"):
            lines.append(f"주의: {dm['caution']}")

    oh = ctx.get("oheng", {})
    if oh.get("found"):
        lines.append(f"\n[{oh.get('label_ko', '')} 재물 패턴]")
        if oh.get("core_theme"):
            lines.append(oh["core_theme"])
        if oh.get("strength"):
            lines.append(f"강점: {oh['strength']}")
        if oh.get("advice"):
            lines.append(f"조언: {oh['advice']}")

    if flow_type:
        flow = get_money_flow_slots(flow_type, seed=seed)
        if flow.get("found"):
            lines.append(f"\n[재물 흐름 — {flow.get('label_ko', '')}]")
            if flow.get("sentence"):
                lines.append(flow["sentence"])

    return "\n".join(lines)
