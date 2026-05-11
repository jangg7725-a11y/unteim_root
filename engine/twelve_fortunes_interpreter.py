# engine/twelve_fortunes_interpreter.py
# -*- coding: utf-8 -*-
"""
십이운성(十二運星) → 심리/에너지 패턴 슬롯 변환기

twelve_fortunes.py 가 계산한 운성 코드를
narrative/twelve_fortunes_pattern_db.json 에서 조회해
behavior_pattern / inner_state / monthly_hint / reframe / strength_zone / friction_zone 슬롯을 반환한다.

사용법:
    from engine.twelve_fortunes_interpreter import get_fortune_stage_slots
    slots = get_fortune_stage_slots(packed)
    monthly = get_monthly_stage_slots(packed)
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.narrative_loader import load_sentences

# ──────────────────────────────────────────────
# 1) DB 로드
# ──────────────────────────────────────────────
_DB_FILE = "twelve_fortunes_pattern_db"


def _db() -> Dict[str, Any]:
    return load_sentences(_DB_FILE)


def _stages() -> Dict[str, Any]:
    return _db().get("stages", {})


# ──────────────────────────────────────────────
# 2) 한국어 → DB 코드 변환
# ──────────────────────────────────────────────
def _stage_map() -> Dict[str, str]:
    return _db().get("engine_mapping", {}).get("stage_map", {})


_HANJA_TO_KO: Dict[str, str] = {
    "長生": "장생", "沐浴": "목욕", "冠帶": "관대", "臨官": "건록",
    "帝旺": "제왕", "衰": "쇠", "病": "병", "死": "사",
    "墓": "묘", "絶": "절", "胎": "태", "養": "양",
}


def _resolve_code(stage_label: str) -> Optional[str]:
    """
    '장생', '목욕', ... 또는 '長生', '沐浴'(한자) 또는 이미 'CHANGSHENG' 형태인 경우 모두 처리.
    """
    label = str(stage_label).strip()
    # 한자 → 한국어 변환
    label = _HANJA_TO_KO.get(label, label)
    smap = _stage_map()
    # 한국어로 들어온 경우
    if label in smap:
        return smap[label]
    # 이미 DB 코드인 경우
    if label.upper() in _stages():
        return label.upper()
    return None


# ──────────────────────────────────────────────
# 3) packed dict 에서 운성 신호 추출
# ──────────────────────────────────────────────
def _extract_stage(packed: Dict[str, Any], pillar: str = "day") -> Optional[str]:
    """
    twelve_fortunes.py 가 생성하는 구조에서 지정 주(柱)의 운성 라벨 추출.

    지원하는 구조:
        packed["twelve_fortunes"][pillar]  → str 라벨
        packed["analysis"]["twelve_fortunes"][pillar] → str
        packed["twelve_fortunes_result"][pillar] → str
    """
    paths = [
        f"twelve_fortunes.{pillar}",
        f"analysis.twelve_fortunes.{pillar}",
        f"twelve_fortunes_result.{pillar}",
        f"twelve_fortunes.items.{pillar}",
    ]
    for path in paths:
        cur: Any = packed
        for key in path.split("."):
            if isinstance(cur, dict) and key in cur:
                cur = cur[key]
            else:
                cur = None
                break
        if isinstance(cur, str) and cur:
            return cur
        if isinstance(cur, dict):
            for key in ("label_ko", "label", "fortune", "name"):
                v = cur.get(key)
                if isinstance(v, str) and v:
                    return v
    return None


def _extract_monthly_stage(packed: Dict[str, Any]) -> Optional[str]:
    """월운 운성 — 월지 기준"""
    paths = [
        "wolwoon.twelve_fortunes",
        "wolwoon.twelve_fortune",
        "monthly.twelve_fortunes",
        "flow.twelve_fortunes.month",
        "twelve_fortunes.month",
    ]
    for path in paths:
        cur: Any = packed
        for key in path.split("."):
            if isinstance(cur, dict) and key in cur:
                cur = cur[key]
            else:
                cur = None
                break
        if isinstance(cur, str) and cur:
            return cur
    return None


# ──────────────────────────────────────────────
# 4) 슬롯 선택 유틸
# ──────────────────────────────────────────────
def _pick(pool: Any, seed: Optional[int] = None) -> str:
    if isinstance(pool, str):
        return pool
    if isinstance(pool, list) and pool:
        return random.Random(seed).choice(pool)
    return ""


# ──────────────────────────────────────────────
# 5) 단일 운성 코드 → 슬롯 dict
# ──────────────────────────────────────────────
def _build_slots(
    code: str,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    stage = _stages().get(code, {})
    if not stage:
        return {}

    phase = stage.get("phase", "")
    is_low_energy = phase in ("declining", "dormant")

    return {
        "code": code,
        "label_ko": stage.get("label_ko", ""),
        "phase": phase,
        "core_energy": stage.get("core_energy", ""),
        "strength_level": stage.get("strength_level", 3),
        "behavior_pattern": _pick(stage.get("behavior_pattern", []), seed),
        "inner_state": _pick(stage.get("inner_state", []), seed),
        "strength_zone": _pick(stage.get("strength_zone", []), seed),
        "friction_zone": _pick(stage.get("friction_zone", []), seed),
        "monthly_hint": _pick(stage.get("monthly_hint", []), seed),
        # 에너지 낮은 국면(declining/dormant)에서만 reframe 우선 주입
        "reframe": stage.get("reframe", "") if is_low_energy else "",
        "reframe_always": stage.get("reframe", ""),
    }


# ──────────────────────────────────────────────
# 6) 조합 힌트 (일주 ↔ 월운 국면 비교)
# ──────────────────────────────────────────────
def _combination_hint(
    day_phase: str,
    monthly_phase: str,
) -> str:
    db = _db()
    hints: Dict[str, Any] = db.get("combination_hints", {})

    if day_phase == "peak" and monthly_phase in ("dormant",):
        return hints.get("peak_on_dormant", {}).get("hint", "")
    if day_phase in ("dormant",) and monthly_phase == "peak":
        return hints.get("dormant_on_peak", {}).get("hint", "")
    if day_phase == monthly_phase:
        return hints.get("same_phase", {}).get("hint", "")
    rising_declining = {
        ("rising", "declining"), ("declining", "rising"),
        ("rising", "dormant"), ("dormant", "rising"),
    }
    if (day_phase, monthly_phase) in rising_declining or (monthly_phase, day_phase) in rising_declining:
        return hints.get("clash_phase", {}).get("hint", "")
    return ""


# ──────────────────────────────────────────────
# 7) 메인 공개 API
# ──────────────────────────────────────────────
def get_fortune_stage_slots(
    packed: Dict[str, Any],
    pillar: str = "day",
    *,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    일주(기본) 기준 십이운성 패턴 슬롯 반환.

    반환:
    {
        "found": bool,
        "code": "JEWANG",
        "label_ko": "제왕",
        "phase": "peak",
        "core_energy": "...",
        "strength_level": 5,
        "behavior_pattern": "...",
        "inner_state": "...",
        "strength_zone": "...",
        "friction_zone": "...",
        "monthly_hint": "...",
        "reframe": "...",         # 에너지 낮은 국면에서만
        "reframe_always": "...",  # 항상 포함
    }
    """
    label = _extract_stage(packed, pillar)
    if not label:
        return {"found": False}

    code = _resolve_code(label)
    if not code:
        return {"found": False}

    slots = _build_slots(code, seed)
    if not slots:
        return {"found": False}

    return {"found": True, **slots}


def get_monthly_stage_slots(
    packed: Dict[str, Any],
    *,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    월운 기준 십이운성 슬롯 반환 + 일주 운성과의 조합 힌트 포함.

    반환:
    {
        "found": bool,
        "monthly": { ... 슬롯 },
        "day": { ... 슬롯 },           # 있을 때만
        "combination_hint": "...",     # 두 국면이 다를 때
    }
    """
    monthly_label = _extract_monthly_stage(packed)
    if not monthly_label:
        return {"found": False}

    monthly_code = _resolve_code(monthly_label)
    if not monthly_code:
        return {"found": False}

    monthly_slots = _build_slots(monthly_code, seed)
    result: Dict[str, Any] = {
        "found": True,
        "monthly": monthly_slots,
    }

    # 일주 운성도 함께 조합
    day_label = _extract_stage(packed, "day")
    if day_label:
        day_code = _resolve_code(day_label)
        if day_code:
            day_slots = _build_slots(day_code, seed)
            result["day"] = day_slots
            hint = _combination_hint(
                day_slots.get("phase", ""),
                monthly_slots.get("phase", ""),
            )
            result["combination_hint"] = hint

    return result


def get_stage_slots_by_label(
    stage_label: str,
    *,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    라벨을 직접 지정해 슬롯을 꺼낼 때.
    예: get_stage_slots_by_label("제왕")
    """
    code = _resolve_code(stage_label)
    if not code:
        return {}
    return _build_slots(code, seed)
