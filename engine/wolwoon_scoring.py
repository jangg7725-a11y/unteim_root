# unteim/engine/wolwoon_scoring.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ScoredPattern:
    id: str
    final_score: int
    trigger_power: int
    gongmang_penalty: int
    breakdown: Dict[str, int]  # 각 항목 점수 기록 (PDF 디버깅용)


def score_pattern(
    pattern_id: str,
    features: Dict[str, Any],
) -> ScoredPattern:
    """
    features 예시 키(엔진에서 채워 넣기):
      - ten_score: int                (십신점수)
      - shinsal_score: int            (신살가중치 합)
      - clash_hap_score: int          (충합 보정)
      - trigger_power: int            (충/합/형파 강도)
      - oheng_adj: int                (오행 보정)
      - unseong_adj: int              (십이운성 보정)
      - gongmang_penalty: int         (공망 패널티: 0 또는 음수)
    """
    ten_score = int(features.get("ten_score", 0))
    shinsal_score = int(features.get("shinsal_score", 0))
    clash_hap_score = int(features.get("clash_hap_score", 0))
    trigger_power = int(features.get("trigger_power", 0))

    oheng_adj = int(features.get("oheng_adj", 0))
    unseong_adj = int(features.get("unseong_adj", 0))
    gongmang_penalty = int(features.get("gongmang_penalty", 0))

    final_score = (
        ten_score
        + shinsal_score
        + clash_hap_score
        + oheng_adj
        + unseong_adj
        + gongmang_penalty
    )

    breakdown = {
        "ten_score": ten_score,
        "shinsal_score": shinsal_score,
        "clash_hap_score": clash_hap_score,
        "oheng_adj": oheng_adj,
        "unseong_adj": unseong_adj,
        "gongmang_penalty": gongmang_penalty,
        "final_score": final_score,
    }

    return ScoredPattern(
        id=pattern_id,
        final_score=final_score,
        trigger_power=trigger_power,
        gongmang_penalty=gongmang_penalty,
        breakdown=breakdown,
    )
