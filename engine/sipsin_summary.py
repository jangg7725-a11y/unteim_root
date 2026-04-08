# unteim/engine/sipsin_summary.py
from __future__ import annotations
from typing import Any, Dict


def sipsin_realism_summary(sipsin: Any) -> str:
    """
    십신 분석 결과(dict)를 "상담용 요약 문장"으로 변환.
    - PDF에 바로 넣어도 어색하지 않게 짧고 현실적인 문장 위주
    """
    if not isinstance(sipsin, dict) or not sipsin:
        return ""

    # 흔히 들어오는 키들(엔진마다 다를 수 있어 안전하게 처리)
    profiles = sipsin.get("profiles") or sipsin.get("profile") or {}
    summary = (sipsin.get("summary") or "").strip()

    # profiles가 dict가 아니면 방어
    if not isinstance(profiles, dict):
        profiles = {}

    # 자주 쓰는 십신/그룹 키 후보
    keys = [
        "비견", "겁재", "식신", "상관", "정재", "편재", "정관", "편관", "정인", "편인",
        "비겁", "식상", "재성", "관성", "인성",
    ]

    parts = []
    for k in keys:
        v = profiles.get(k)
        if v is None:
            continue
        try:
            n = int(v)
        except Exception:
            continue
        if n > 0:
            parts.append(f"{k}×{n}")

    line1 = ""
    if parts:
        line1 = f"십신 분포(요약): " + ", ".join(parts)

    # summary가 비어있으면 최소 문장 생성
    if not summary:
        if parts:
            summary = "현재는 강점이 드러나는 축과 약한 축이 함께 보입니다. 강점은 살리고, 약한 부분은 루틴으로 보완하는 쪽이 좋습니다."
        else:
            summary = "십신 요약 데이터가 단순 형태라, 상세 해석은 후속 고도화 구간에서 더 정확해집니다."

    # PDF에 2~3줄 정도만
    out = []
    if line1:
        out.append(line1)
    out.append(summary)

    return "\n".join(out).strip()
