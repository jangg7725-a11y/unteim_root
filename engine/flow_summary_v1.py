# unteim/engine/flow_summary_v1.py
from __future__ import annotations

from typing import Any, Dict

from engine.hap_chung_interpreter import get_relation_pattern_slots

def build_flow_summary_v1(
    base: Dict[str, Any],
    daewoon: Dict[str, Any] | None = None,
    sewun: Dict[str, Any] | None = None,
    wolwoon: Dict[str, Any] | None = None,
    verbosity: str = "standard",  # "short" | "standard" | "long"
) -> Dict[str, Any]:

    """
    흐름 요약(대운/세운/월운) 표준 오브젝트 생성기 v1

    - base: {"oheng":..., "sipsin":..., "yongshin":..., "shinsal":..., "kongmang":..., "twelve_fortunes":..., ...}
    - daewoon/sewun/wolwoon: _norm_luck_obj()로 만든 dict (없으면 None 가능)

    반환:
    {
      "daewoon": {...} | None,
      "sewun": {...} | None,
      "wolwoon": {...} | None
    }
    """
    out: Dict[str, Any] = {}

    # short: 핵심만 (카드/위젯)
    if verbosity == "short":
        if isinstance(sewun, dict):
            out["sewun"] = sewun
        elif isinstance(wolwoon, dict):
            out["wolwoon"] = wolwoon
        # base는 short에서 제외 (요약 카드용)

    # standard: 현재 기본 (앱/PDF 기본)
    elif verbosity == "standard":
        out["daewoon"] = daewoon if isinstance(daewoon, dict) else None
        out["sewun"] = sewun if isinstance(sewun, dict) else None
        out["wolwoon"] = wolwoon if isinstance(wolwoon, dict) else None
        if isinstance(base, dict):
            out["base"] = base

    # long: 전체 (상담/확장)
    else:
        out["daewoon"] = daewoon if isinstance(daewoon, dict) else None
        out["sewun"] = sewun if isinstance(sewun, dict) else None
        out["wolwoon"] = wolwoon if isinstance(wolwoon, dict) else None
        if isinstance(base, dict):
            out["base"] = base
            # long에서만 base 확장 키 허용
            for k in ("oheng", "sipsin", "yongshin", "shinsal", "kongmang"):
                if k in base:
                    out[k] = base.get(k)

    _rel = get_relation_pattern_slots(base if isinstance(base, dict) else {})
    if _rel["found"]:
        out["relation_pattern"] = _rel["relation_pattern"]
        out["relation_reframe"] = _rel["reframe"]
        out["relation_caution"] = _rel["caution"]

    return out

