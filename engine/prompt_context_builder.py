# -*- coding: utf-8 -*-
"""
engine/prompt_context_builder.py

P3-1: 명리 DB 슬롯 → GPT 프롬프트 컨텍스트 주입 엔진

역할:
  - daymaster / geukguk / kongmang / hap_chung / shinsal / twelve_fortunes
    인터프리터에서 랜덤 슬롯 문장을 수집하여
  - counsel_summary.py의 섹션에 감정언어 레이어로 덧붙임
  - counsel_service.py의 SYSTEM_TEMPLATE {analysis_summary} 안에 자연스럽게 주입

사용법:
    from engine.prompt_context_builder import build_psychology_context

    ctx = build_psychology_context(report, profile)
    # ctx는 str → analysis_summary 끝에 append

구조:
    build_psychology_context(report, profile, intent="general")
      ├── _get_daymaster_ctx(report, profile)
      ├── _get_geukguk_ctx(report)
      ├── _get_kongmang_ctx(report)
      ├── _get_shinsal_ctx(report)
      ├── _get_twelve_fortunes_ctx(report)
      └── _get_hap_chung_ctx(report)
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

# ── 인터프리터 임포트 (없으면 graceful skip) ──────────────────────
try:
    from engine.daymaster_psychology_interpreter import get_daymaster_slots
    _HAS_DAYMASTER = True
except ImportError:
    _HAS_DAYMASTER = False

try:
    from engine.geukguk_narrative_interpreter import get_geukguk_slots
    _HAS_GEUKGUK = True
except ImportError:
    _HAS_GEUKGUK = False

try:
    from engine.kongmang_pattern_interpreter import get_kongmang_slots
    _HAS_KONGMANG = True
except ImportError:
    _HAS_KONGMANG = False

try:
    from engine.shinsal_psychology_interpreter import get_shinsal_psychology_slots
    _HAS_SHINSAL = True
except ImportError:
    _HAS_SHINSAL = False

try:
    from engine.twelve_fortunes_interpreter import get_fortune_stage_slots
    _HAS_TWELVE = True
except ImportError:
    _HAS_TWELVE = False

try:
    from engine.hap_chung_interpreter import get_relation_pattern_slots
    _HAS_HAP = True
except ImportError:
    _HAS_HAP = False


# ── intent별 주입 슬롯 우선순위 ────────────────────────────────────
# 토픽에 따라 어떤 DB 슬롯을 먼저 / 더 많이 주입할지 결정
INTENT_SLOT_PRIORITY: Dict[str, List[str]] = {
    "personality": [
        "identity", "inner_state", "behavior", "reframe",
        "strength", "life_theme", "stress",
    ],
    "relationship": [
        "relation", "inner_state", "behavior", "reframe",
        "stress", "identity",
    ],
    "wealth": [
        "career", "strength", "behavior", "monthly_advice",
        "life_theme", "reframe",
    ],
    "work": [
        "career", "strength", "behavior", "monthly_advice",
        "reframe", "growth",
    ],
    "health": [
        "stress", "inner_state", "monthly_advice", "reframe",
        "behavior",
    ],
    "exam": [
        "strength", "behavior", "monthly_advice", "career",
        "reframe",
    ],
    "general": [
        "identity", "inner_state", "behavior", "relation",
        "reframe", "monthly_advice",
    ],
}

# intent별 최대 주입 슬롯 수 (토큰 절약)
INTENT_MAX_SLOTS: Dict[str, int] = {
    "personality": 5,
    "relationship": 4,
    "wealth": 4,
    "work": 4,
    "health": 3,
    "exam": 3,
    "general": 4,
}


def _safe_str(v: Any) -> str:
    return str(v).strip() if v else ""


def _pick(slots: Dict[str, Any], key: str) -> str:
    """슬롯 dict에서 key 값을 꺼냄 (문자열 보장)."""
    return _safe_str(slots.get(key, ""))


# ── 개별 DB 컨텍스트 빌더 ──────────────────────────────────────────

def _get_daymaster_ctx(
    report: Dict[str, Any],
    profile: Dict[str, Any],
    intent: str,
    seed: Optional[int] = None,
) -> Optional[str]:
    """일간 심리 프로파일 → 감정언어 컨텍스트 블록."""
    if not _HAS_DAYMASTER:
        return None

    # 일간 추출 경로
    a = report.get("analysis") or report.get("saju") or {}
    dm_obj = a.get("day_master") or {}
    gan = (
        dm_obj.get("gan")
        or dm_obj.get("label")
        or profile.get("day_gan")
        or profile.get("dayGan")
        or ""
    )
    if not gan:
        return None

    slots = get_daymaster_slots(gan, seed=seed)
    if not isinstance(slots, dict) or slots.get("found") is False:
        return None

    priority = INTENT_SLOT_PRIORITY.get(intent, INTENT_SLOT_PRIORITY["general"])
    max_n = INTENT_MAX_SLOTS.get(intent, 4)

    lines: List[str] = []
    label = _pick(slots, "label") or gan
    core_image = _pick(slots, "core_image")

    header = f"[일간 심리 — {label}]"
    if core_image:
        header += f"  ※ {core_image}"
    lines.append(header)

    count = 0
    for slot_key in priority:
        if count >= max_n:
            break
        sentence = _pick(slots, slot_key)
        if sentence:
            lines.append(f"• {sentence}")
            count += 1

    if len(lines) <= 1:
        return None
    return "\n".join(lines)


def _get_geukguk_ctx(
    report: Dict[str, Any],
    intent: str,
    seed: Optional[int] = None,
) -> Optional[str]:
    """격국 인생서사 → 감정언어 컨텍스트 블록."""
    if not _HAS_GEUKGUK:
        return None

    # 격국명 추출
    bs = report.get("basicSaju") or report.get("basic_saju") or report
    gk_obj = bs.get("geukguk") or {}
    gk_name = (
        gk_obj.get("label")
        or gk_obj.get("name")
        or (str(gk_obj).strip() if isinstance(gk_obj, str) else "")
    )
    if not gk_name:
        # analyze_full 결과 다른 경로 시도
        a = report.get("analysis") or {}
        gk_name = _safe_str(a.get("geukguk") or "")
    if not gk_name:
        return None

    slots = get_geukguk_slots(gk_name, seed=seed)
    if not isinstance(slots, dict) or slots.get("found") is False:
        return None

    priority = INTENT_SLOT_PRIORITY.get(intent, INTENT_SLOT_PRIORITY["general"])
    max_n = INTENT_MAX_SLOTS.get(intent, 4)

    lines: List[str] = []
    label = _pick(slots, "label_ko") or gk_name
    core_narrative = _pick(slots, "core_narrative")

    header = f"[격국 서사 — {label}]"
    if core_narrative:
        header += f"  ※ {core_narrative}"
    lines.append(header)

    count = 0
    for slot_key in priority:
        if count >= max_n:
            break
        sentence = _pick(slots, slot_key)
        if sentence:
            lines.append(f"• {sentence}")
            count += 1

    if len(lines) <= 1:
        return None
    return "\n".join(lines)


def _get_kongmang_ctx(
    report: Dict[str, Any],
    intent: str,
    seed: Optional[int] = None,
) -> Optional[str]:
    """공망 감정패턴 → 컨텍스트 블록 (공망 있는 주만)."""
    if not _HAS_KONGMANG:
        return None

    # 공망 flags 추출
    km_obj = (
        report.get("kongmang")
        or report.get("kongwang")
        or {}
    )
    flags: Dict[str, bool] = km_obj.get("flags") or {}
    active_pillars = [p for p, v in flags.items() if v]
    if not active_pillars:
        return None

    priority = INTENT_SLOT_PRIORITY.get(intent, INTENT_SLOT_PRIORITY["general"])
    max_n = max(2, INTENT_MAX_SLOTS.get(intent, 4) // 2)  # 공망은 절반만

    blocks: List[str] = []
    for i, pillar in enumerate(active_pillars[:2]):  # 최대 2개 주까지만
        sub_seed = (seed + i) if seed is not None else None
        slots = get_kongmang_slots(pillar, seed=sub_seed)
        if not isinstance(slots, dict) or slots.get("found") is False:
            continue
        label = _pick(slots, "label_ko") or f"{pillar}주 공망"
        core_meaning = _pick(slots, "core_meaning")
        sub: List[str] = [f"[{label}]"]
        if core_meaning:
            sub.append(f"  ※ {core_meaning}")
        count = 0
        for slot_key in priority:
            if count >= max_n:
                break
            sentence = _pick(slots, slot_key)
            if sentence:
                sub.append(f"• {sentence}")
                count += 1
        if len(sub) > 1:
            blocks.append("\n".join(sub))

    if not blocks:
        return None
    return "\n".join(blocks)


# 신살 슬롯 필드 (일반 슬롯명과 다름)
_SHINSAL_FIELDS_BY_INTENT: Dict[str, List[str]] = {
    "personality": [
        "dominant_trait", "inner_state", "behavior_pattern",
        "reframe", "caution",
    ],
    "relationship": [
        "relation_pattern", "inner_state", "behavior_pattern",
        "dominant_trait", "reframe",
    ],
    "wealth": [
        "dominant_trait", "behavior_pattern", "caution",
        "inner_state", "reframe",
    ],
    "work": [
        "dominant_trait", "behavior_pattern", "caution",
        "inner_state", "reframe",
    ],
    "health": [
        "stress_response", "inner_state", "caution",
        "behavior_pattern", "dominant_trait",
    ],
    "exam": [
        "dominant_trait", "behavior_pattern", "inner_state",
        "caution", "reframe",
    ],
    "general": [
        "dominant_trait", "behavior_pattern", "inner_state",
        "relation_pattern", "reframe",
    ],
}


def _get_shinsal_ctx(
    report: Dict[str, Any],
    intent: str,
    seed: Optional[int] = None,
) -> Optional[str]:
    """신살 심리 → 컨텍스트 블록 (상위 2개)."""
    if not _HAS_SHINSAL:
        return None

    bundle = get_shinsal_psychology_slots(report, seed=seed, max_items=2)
    if not bundle.get("found") or not bundle.get("items"):
        return None

    field_order = _SHINSAL_FIELDS_BY_INTENT.get(
        intent, _SHINSAL_FIELDS_BY_INTENT["general"]
    )
    max_n = max(2, INTENT_MAX_SLOTS.get(intent, 4) // 2)

    blocks: List[str] = []
    for item in bundle["items"][:2]:
        label = _pick(item, "label_ko") or _pick(item, "shinsal_id") or "신살"
        sub: List[str] = [f"[신살 — {label}]"]
        count = 0
        for field in field_order:
            if count >= max_n:
                break
            sentence = _pick(item, field)
            if sentence:
                sub.append(f"• {sentence}")
                count += 1
        if len(sub) > 1:
            blocks.append("\n".join(sub))

    hint = _safe_str(bundle.get("combination_hint"))
    if hint and len(bundle["items"]) >= 2:
        blocks.append(f"[신살 조합]\n• {hint}")

    if not blocks:
        return None
    return "\n".join(blocks)


_TWELVE_ORDER: List[str] = [
    "core_energy",
    "behavior_pattern",
    "inner_state",
    "reframe",
    "monthly_hint",
    "strength_zone",
    "friction_zone",
]


def _get_twelve_fortunes_ctx(
    report: Dict[str, Any],
    intent: str,
    seed: Optional[int] = None,
) -> Optional[str]:
    """십이운성 → 일주 기준 운성 단계 컨텍스트."""
    if not _HAS_TWELVE:
        return None

    slots = get_fortune_stage_slots(report, pillar="day", seed=seed)
    if not isinstance(slots, dict) or slots.get("found") is False:
        return None

    label = _pick(slots, "label_ko") or ""
    header = f"[십이운성 — {label}]" if label else "[십이운성]"
    max_n = min(4, INTENT_MAX_SLOTS.get(intent, 4))

    lines: List[str] = [header]
    count = 0
    for slot_key in _TWELVE_ORDER:
        if count >= max_n:
            break
        sentence = _pick(slots, slot_key)
        if sentence:
            lines.append(f"• {sentence}")
            count += 1

    if len(lines) <= 1:
        return None
    return "\n".join(lines)


_HAP_ORDER: List[str] = [
    "relation_pattern",
    "inner_state",
    "behavior_pattern",
    "reframe",
]


def _get_hap_chung_ctx(
    report: Dict[str, Any],
    intent: str,
    seed: Optional[int] = None,
) -> Optional[str]:
    """합충형파해 → 관계·심리 컨텍스트 (일부 intent만)."""
    if not _HAS_HAP:
        return None
    if intent not in ("relationship", "general", "personality"):
        return None

    slots = get_relation_pattern_slots(report, seed=seed, max_items=1)
    if not isinstance(slots, dict) or not slots.get("found"):
        return None

    items = slots.get("items") or []
    label = ""
    if items:
        label = _pick(items[0], "label")
    label = label or _pick(slots, "relation_pattern") or "관계 패턴"

    sub: List[str] = [f"[합충 — {label}]"]
    max_n = 3
    count = 0
    for slot_key in _HAP_ORDER:
        if count >= max_n:
            break
        sentence = _pick(slots, slot_key)
        if sentence:
            sub.append(f"• {sentence}")
            count += 1

    if len(sub) <= 1:
        return None
    return "\n".join(sub)


# ── 메인 함수 ──────────────────────────────────────────────────────

def build_psychology_context(
    report: Dict[str, Any],
    profile: Dict[str, Any],
    intent: str = "general",
    *,
    seed: Optional[int] = None,
) -> str:
    """
    모든 DB 슬롯을 수집해 GPT 프롬프트에 주입할
    [감정언어 심리 컨텍스트] 블록을 반환한다.

    반환값은 counsel_summary의 analysis_summary 끝에 append하면 된다.

    Parameters
    ----------
    report  : analyze_full() 결과 dict
    profile : 사용자 프로필 dict (day_gan 등 포함)
    intent  : 상담 의도 (personality / relationship / wealth / work / health / exam / general)
    seed    : 랜덤 시드 (테스트용)

    Returns
    -------
    str : 프롬프트에 삽입할 텍스트 블록 (비어있으면 "")
    """
    if seed is not None:
        random.seed(seed)

    intent_key = intent if intent in INTENT_SLOT_PRIORITY else "general"

    blocks: List[str] = []

    # 1. 일간 (가장 핵심 — 항상 최우선)
    dm = _get_daymaster_ctx(report, profile, intent_key, seed)
    if dm:
        blocks.append(dm)

    # 2. 격국 (인생 서사)
    gk = _get_geukguk_ctx(report, intent_key, seed)
    if gk:
        blocks.append(gk)

    # 3. 공망 (해당 주 있을 때만)
    km = _get_kongmang_ctx(report, intent_key, seed)
    if km:
        blocks.append(km)

    # 4. 신살 (상위 2개)
    sh = _get_shinsal_ctx(report, intent_key, seed)
    if sh:
        blocks.append(sh)

    # 5. 십이운성 (일주 운성)
    tf = _get_twelve_fortunes_ctx(report, intent_key, seed)
    if tf:
        blocks.append(tf)

    # 6. 합충 (관계 토픽일 때)
    hc = _get_hap_chung_ctx(report, intent_key, seed)
    if hc:
        blocks.append(hc)

    if not blocks:
        return ""

    header = (
        "\n\n【감정언어 심리 컨텍스트 — AI는 아래 문장을 답변의 심리·행동 해석 근거로 활용하세요】\n"
        "※ 아래는 운트임 명리 DB에서 추출한 이 사람의 심리·행동 패턴입니다. "
        "사주 계산 결과와 함께 연결해 공감·해석·원인 설명에 자연스럽게 녹여 쓰세요. "
        "문장을 그대로 복사하지 말고 대화에 맞게 풀어 쓰세요.\n"
    )
    return header + "\n\n".join(blocks)


def inject_into_summary(
    analysis_summary: str,
    report: Dict[str, Any],
    profile: Dict[str, Any],
    intent: str = "general",
    *,
    seed: Optional[int] = None,
) -> str:
    """
    기존 analysis_summary 문자열 끝에 심리 컨텍스트를 append해 반환.

    counsel_service.py에서:
        analysis_summary = inject_into_summary(
            analysis_summary, _report, profile, intent=intent
        )
    한 줄 추가만으로 연결됩니다.
    """
    ctx = build_psychology_context(report, profile, intent, seed=seed)
    if not ctx:
        return analysis_summary
    return (analysis_summary or "").rstrip() + "\n" + ctx
