# unteim/engine/shinsal_summary.py
from __future__ import annotations
from typing import Any, Dict, List


def shinsal_hint_sentence(items: List[Dict[str, Any]]) -> str:
    """
    신살 리스트(한 기둥/그룹)를 받아 상담용 '요약 문장' 2~3줄 생성.
    items: detect_shinsal 결과의 일부 (dict들의 리스트)
    """
    if not items:
        return ""

    # name/key/type/desc/detail 중에서 최대한 뽑기
    names = []
    for row in items[:6]:
        if not isinstance(row, dict):
            continue
        nm = row.get("name") or row.get("key") or row.get("type")
        if nm and str(nm).strip():
            names.append(str(nm).strip())

    names = [n for i, n in enumerate(names) if n and n not in names[:i]]
    if not names:
        return ""

    headline = "주요 신살: " + ", ".join(names[:6])

    # 아주 보수적인(안전한) 요약 문장 템플릿
    # (세부 신살 의미는 later: shinsal_explainer.py 연동 시 더 정밀화 가능)
    guide = (
        "포인트: 해당 기둥에서 사건/사람/관계의 '특수한 결'이 잘 잡힙니다.\n"
        "추천 액션: 좋은 흐름은 기록·점검으로 고정하고, 불안정 신호는 일정/계약/관계에서 확인 절차를 강화하세요."
    )

    return f"{headline}\n{guide}"
