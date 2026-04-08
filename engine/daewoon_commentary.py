# unteim/engine/daewoon_commentary.py
from __future__ import annotations
from typing import Any, Dict, List


def _fmt_age(v: Any) -> str:
    try:
        return f"{float(v):.2f}"
    except Exception:
        return ""


def analyze_daewoon_commentary(
    daewoon_list: List[Dict[str, Any]],
    yongshin: Any = None,
    oheng: Any = None,
) -> str:
    if not daewoon_list:
        return ""

    lines: List[str] = []
    lines.append("대운은(는) ‘흐름의 지도’입니다. 좋은 때는 확장/시도, 주의 구간은 정리/방어를 하면 체감이 확 달라집니다.")

    for it in daewoon_list:
        start = _fmt_age(it.get("start_age"))
        end = _fmt_age(it.get("end_age"))
        pillar = str(it.get("pillar", "")).strip()

        if not (start and end and pillar):
            continue

        lines.append(f"- {start}~{end}세 : {pillar} 구간 → 기반을 다지고 방향을 잡는 흐름. 무리한 승부보다 ‘리듬 관리’가 핵심입니다.")

    return "\n".join(lines)
