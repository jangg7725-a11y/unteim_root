"""
report_yongshin_luck_adapter.py
대운/세운 + 월운(flow) + 용신/희신/기신 조합으로
'언제 운이 열리고 조심해야 하는지'를 리포트에 추가하는 어댑터
"""

from __future__ import annotations
from typing import Dict, Any, List

from engine.yongshin_luck import analyze_yongshin_luck


def enrich_report_with_yongshin_luck(report: Dict[str, Any]) -> Dict[str, Any]:
    # pillars 안에 용신 정보가 들어있다고 가정
    pillars = report.get("pillars") or {}

    dayun_list: List[Dict[str, Any]] = report.get("dayun") or []
    seyun_list: List[Dict[str, Any]] = report.get("seyun") or report.get("seun") or []
    monthly_flow: List[Dict[str, Any]] = report.get("flow") or []

    yongshin_info = pillars.get("yongshin_info") or pillars.get("yongshin")

    luck_result = analyze_yongshin_luck(
        dayun_list,
        seyun_list,
        monthly_flow,
        yongshin_info,
    )

    # 결과 전체를 통째로 리포트에 실어줌
    report["yongshin_luck"] = luck_result

    return report
