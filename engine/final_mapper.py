# unteim/engine/final_mapper.py
from __future__ import annotations
from typing import Any, Dict


def compose_final_mapping(
    *,
    elements: Dict[str, Any],   # 오행/기세/강약
    yong_meta: Dict[str, Any],  # 용신/희신/기신
    ten_gods: Dict[str, Any],   # 십신 요약/분포
    luck_stack: Dict[str, Any], # 대운/세운/월운 + 십신축
    conflicts: Dict[str, Any],  # 형/충/합 등 이벤트 방식
    shinsal: Dict[str, Any],    # 신살 요약(강조/보정만)
) -> Dict[str, Any]:
    """
    최종 매핑 원칙:
    1) 계산은 분리
    2) 출력 직전 1회 통합
    3) 신살은 단독 해석 금지(강조/보정 only)
    4) 용/희/기신은 십신/운 해석 방향키로 적용
    """
    final: Dict[str, Any] = {}

    final["elements"] = elements
    final["yong_meta"] = yong_meta
    final["ten_gods"] = ten_gods
    final["luck_stack"] = luck_stack
    final["conflicts"] = conflicts

    # 신살은 "tone/flags"로만 부착 (주인공 금지)
    final["shinsal_tone"] = {
        "summary": shinsal.get("summary", ""),
        "risk_flags": shinsal.get("risk_flags", []),
        "support_flags": shinsal.get("support_flags", []),
        "items": shinsal.get("items", []),
    }

    # 합성 결과를 한 번 더 요약 키로 제공(리포트/프롬프트 공용)
    final["mapping_rule"] = {
        "pipeline": "elements -> yong/heui/gi -> luck×ten_gods -> conflicts -> shinsal_tone",
        "note": "separate compute, compose once before output",
    }

    return final
