# unteim/engine/month_narrative_basic.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from engine.narrative.report_narrative import build_month_basic_narrative as _build_from_store


def build_month_basic_narrative(
    *,
    birth_str: str = "",
    when: str = "",
    oheng: Optional[Dict[str, Any]] = None,
    shinsal: Optional[Dict[str, Any]] = None,
    wolwoon_top3: Any = None,
    yongshin: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    월간 요약/주의/실행 문장 — narrative/*.json + report_narrative에서 생성합니다.
    yongshin: analysis.yongshin 형태의 dict( element 키 포함 )
    """
    return _build_from_store(
        birth_str=birth_str,
        when=when,
        oheng=oheng,
        shinsal=shinsal,
        wolwoon_top3=wolwoon_top3,
        yongshin=yongshin,
    )
