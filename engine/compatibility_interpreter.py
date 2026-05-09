# engine/compatibility_interpreter.py
# -*- coding: utf-8 -*-
"""
10천간 × 10천간 관계 매트릭스 → GPT 궁합·역학 슬롯

narrative/compatibility_matrix_db.json 의 combinations 조회.
키: my_gan + '_' + partner_gan (한자 간지 기준 권장), 없으면 역순 키 시도.
"""

from __future__ import annotations

import random
from typing import Any, Dict, Optional, Tuple

from utils.narrative_loader import load_sentences

_DB_FILE = "compatibility_matrix_db"

_GAN_ALIAS: Dict[str, str] = {
    "甲": "甲", "갑": "甲", "갑목": "甲",
    "乙": "乙", "을": "乙", "을목": "乙",
    "丙": "丙", "병": "丙", "병화": "丙",
    "丁": "丁", "정": "丁", "정화": "丁",
    "戊": "戊", "무": "戊", "무토": "戊",
    "己": "己", "기": "己", "기토": "己",
    "庚": "庚", "경": "庚", "경금": "庚",
    "辛": "辛", "신": "辛", "신금": "辛",
    "壬": "壬", "임": "壬", "임수": "壬",
    "癸": "癸", "계": "癸", "계수": "癸",
}


def _db() -> Dict[str, Any]:
    return load_sentences(_DB_FILE)


def _combinations() -> Dict[str, Any]:
    return _db().get("combinations", {})


def _normalize_gan(gan: Any) -> str:
    raw = str(gan).strip()
    if not raw:
        return ""
    if raw in _GAN_ALIAS:
        return _GAN_ALIAS[raw]
    return raw


def _pick(pool: Any, rng: random.Random) -> str:
    if isinstance(pool, str) and pool.strip():
        return pool.strip()
    if isinstance(pool, list) and pool:
        return str(rng.choice(pool)).strip()
    return ""


def _lookup_entry(my_g: str, partner_g: str) -> Tuple[Optional[Dict[str, Any]], str, bool]:
    """
    (entry_dict, 실제 매칭 키, 역순으로 찾았는지 여부).
    """
    combos = _combinations()
    k_forward = f"{my_g}_{partner_g}"
    if k_forward in combos:
        entry = combos.get(k_forward)
        if isinstance(entry, dict):
            return entry, k_forward, False

    k_rev = f"{partner_g}_{my_g}"
    if k_rev in combos:
        entry = combos.get(k_rev)
        if isinstance(entry, dict):
            return entry, k_rev, True

    return None, "", False


def get_compatibility_slots(
    my_gan: Any,
    partner_gan: Any,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    두 일간 문자로 매트릭스 조합을 찾아 풀마다 랜덤 1문장을 반환.

    반환 필드:
        found, lookup_key (매칭 키), used_reverse_lookup (역순 키 참조 여부),
        label, mingri_relation, core_dynamic,
        dynamic, strength, friction, growth, daily_hint
    """
    my_g = _normalize_gan(my_gan)
    partner_g = _normalize_gan(partner_gan)
    if not my_g or not partner_g:
        return {"found": False}

    entry, lk, rev = _lookup_entry(my_g, partner_g)
    if entry is None:
        return {"found": False}

    rng = random.Random(seed)
    meta = {
        "found": True,
        "lookup_key": lk,
        "used_reverse_lookup": rev,
        "label": entry.get("label") or lk,
        "mingri_relation": entry.get("mingri_relation") or "",
        "core_dynamic": entry.get("core_dynamic") or "",
        "dynamic": _pick(entry.get("dynamic_pool", []), rng),
        "strength": _pick(entry.get("strength_pool", []), rng),
        "friction": _pick(entry.get("friction_pool", []), rng),
        "growth": _pick(entry.get("growth_pool", []), rng),
        "daily_hint": _pick(entry.get("daily_hint_pool", []), rng),
    }
    return meta


def get_compatibility_summary(
    my_gan: Any,
    partner_gan: Any,
    seed: Optional[int] = None,
) -> str:
    """
    get_compatibility_slots 결과를 GPT system 프롬프트 삽입용 문자열로 정리한다.
    조합이 없으면 빈 문자열.
    """
    s = get_compatibility_slots(my_gan, partner_gan, seed=seed)
    if not s.get("found"):
        return ""

    lines = [
        "【천간 궁합·관계 역학 참고 — 사주 근거와 함께 활용하고, 단정·이분법 피해서 풀어 쓰세요】",
        f"· 조합: {_fmt(s.get('label'))}",
        f"· 명리 관계: {_fmt(s.get('mingri_relation'))}",
        f"· 역학 요약: {_fmt(s.get('core_dynamic'))}",
        f"· 관계 역학: {_fmt(s.get('dynamic'))}",
        f"· 강점: {_fmt(s.get('strength'))}",
        f"· 마찰(차이): {_fmt(s.get('friction'))}",
        f"· 함께 성장: {_fmt(s.get('growth'))}",
        f"· 일상 팁: {_fmt(s.get('daily_hint'))}",
    ]
    if s.get("used_reverse_lookup"):
        lines.insert(
            2,
            f"· (조회 참고키: {_fmt(s.get('lookup_key'))} — 상반된 시점 각도의 매트릭스 참조)",
        )
    text = "\n".join(lines)
    return "\n\n" + text


def _fmt(v: Any) -> str:
    return str(v).strip() if v else ""
