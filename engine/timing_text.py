# unteim/engine/timing_text.py
from __future__ import annotations
from typing import Any, Dict, List

def _safe(v: Any) -> str:
    return "" if v is None else str(v)

def build_daewoon_text(daewoon: List[Dict[str, Any]], ctx: Dict[str, Any]) -> str:
    """
    대운 요약 해석(1차 뼈대)
    - 지금은 '표 데이터 기반'으로만 문장 생성
    - 이후: 용신/희신/기신 + 신살 + 오행 기세 흐름까지 연결 예정
    """
    if not daewoon:
        return "대운 데이터가 아직 충분히 준비되지 않아 요약 해석을 생략합니다."

    first = daewoon[0]
    last = daewoon[-1]
    return (
        f"대운은 약 { _safe(first.get('start_age')) }세부터 시작하여 "
        f"{ _safe(last.get('end_age')) }세 무렵까지 흐름이 이어집니다.\n"
        f"현재 출력은 1차 표 기반 요약이며, 다음 고도화 단계에서 "
        f"용신/희신/기신 및 오행 기세 흐름을 결합해 '좋은 구간/주의 구간'을 문장으로 확정합니다."
    )

def build_sewun_text(sewun: List[Dict[str, Any]], ctx: Dict[str, Any]) -> str:
    if not sewun:
        return "세운 데이터가 아직 충분히 준비되지 않아 요약 해석을 생략합니다."

    # 샘플: 앞 3년만 뽑아 “흐름 안내”
    top = sewun[:3]
    lines = []
    for it in top:
        y = _safe(it.get("year"))
        lab = _safe(it.get("label"))
        lines.append(f"- {y}년: {lab}")
    return (
        "세운은 해마다 기운이 바뀌며, 현재는 '연주(간지)' 중심으로 샘플을 제공합니다.\n"
        + "\n".join(lines)
        + "\n\n다음 고도화 단계에서 용신/기신과의 상생·상극, 그리고 신살 발동까지 합쳐 "
        "해마다의 '운의 성격(일/관/재/인/식 중심)'을 문장으로 확정합니다."
    )

from engine.commentary_input import from_final_mapping

def build_wolwoon_text(
    *,
    final_mapping: dict,
    wolwoon: List[Dict[str, Any]],
    verbosity: str = "standard",
) -> str:
    ctx = from_final_mapping(final_mapping)

    if not wolwoon:
        return "월운 데이터가 아직 충분히 준비되지 않아 요약 해석을 생략합니다."


    # 샘플: 1~3월만 표시
    top = wolwoon[:3]
    lines = []
    for it in top:
        y = _safe(it.get("year"))
        m = _safe(it.get("month"))
        lab = _safe(it.get("label"))
        lines.append(f"- {y}년 {m}월: {lab}")
    return (
        "월운은 실전 체감이 가장 빠른 흐름입니다. 현재는 '월 라벨' 중심 샘플을 제공합니다.\n"
        + "\n".join(lines)
        + "\n\n다음 고도화 단계에서 월운을 용신/희신/기신과 대조해 "
        "'이번 달은 밀어붙일 달/정리할 달' 같은 코칭 문장으로 바꿉니다."
    )
