# unteim/engine/geukguk_engine.py
from __future__ import annotations

from typing import Any, Dict, Optional

from .types import SajuPillars, coerce_pillars

# sipsin.py 안에 ten_god(일간, 상대천간) 형태가 이미 있다고 가정
# (없거나 이름이 다르면 아래 import 줄만 맞춰주면 됩니다)
from .sipsin import ten_god


# 천간 오행 매핑 (필요 최소)
_GAN_ELEMENT = {
    "갑": "목", "을": "목",
    "병": "화", "정": "화",
    "무": "토", "기": "토",
    "경": "금", "신": "금",
    "임": "수", "계": "수",
}

# 십신 → 축(axis) 매핑 (운트임 표준)
_TENGOD_AXIS = {
    "정인": "인성", "편인": "인성",
    "식신": "식상", "상관": "식상",
    "정재": "재성", "편재": "재성",
    "정관": "관성", "편관": "관성",
    "비견": "비겁", "겁재": "비겁",
}

# 축(axis) → 격국명(간단형) 매핑
_AXIS_GUK = {
    "인성": "인성격",
    "식상": "식상격",
    "재성": "재성격",
    "관성": "관성격",
    "비겁": "비겁격",
}


def _safe_get_gan(p: Any, pillar_name: str) -> Optional[str]:
    """
    SajuPillars 내부 구조가 조금 달라도 최대한 뽑아내기 위한 방어 함수.
    기대 형태:
      p.day.gan, p.month.gan, ... 또는
      p["day"]["gan"], p["month"]["gan"] ...
    """
    # object attribute 우선
    pillar = getattr(p, pillar_name, None)
    if pillar is not None:
        gan = getattr(pillar, "gan", None)
        if gan:
            return gan

        # 혹시 ganji 형태라면
        ganji = getattr(pillar, "ganji", None)
        if isinstance(ganji, dict):
            v = ganji.get("gan")
            if v:
                return v

    # dict 형태 fallback
    if isinstance(p, dict):
        pillar = p.get(pillar_name)
        if isinstance(pillar, dict):
            gan = pillar.get("gan")
            if gan:
                return gan
            ganji = pillar.get("ganji")
            if isinstance(ganji, dict):
                v = ganji.get("gan")
                if v:
                    return v

    return None


def analyze_geukguk(
    pillars: Any,
    *,
    oheng_summary: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    운트임 최소 안정판 격국(geukguk) 판정기.

    기준:
    - 월간(월주 천간)의 십신을 일간 기준으로 산출 → dominant_tengod
    - dominant_tengod → axis 매핑
    - axis → 간단 격국명 매핑 (인성격/식상격/재성격/관성격/비겁격)
    - 구조 타입(structure_type)은 아직 '초기판'으로만 분류
    """
    p = coerce_pillars(pillars)

    day_gan = _safe_get_gan(p, "day")
    month_gan = _safe_get_gan(p, "month")

    dominant_tengod = None
    axis = None

    if day_gan and month_gan:
        try:
            dominant_tengod = ten_god(day_gan, month_gan)
        except Exception:
            dominant_tengod = None

    if dominant_tengod:
        axis = _TENGOD_AXIS.get(dominant_tengod)

    # 격국명
    name = _AXIS_GUK.get(axis or "", "혼합형")

    # 월간 오행
    dominant_element = _GAN_ELEMENT.get(month_gan, None) if month_gan else None

    # 구조 타입(초기판): 오행 요약이 있으면 과다/약화 정도만 판정
    structure_type = "균형형"
    if oheng_summary and isinstance(oheng_summary, dict):
        # 기대: {"counts": {"목":x,"화":y...}} 또는 {"five":{...}} 등
        counts = None
        if isinstance(oheng_summary.get("counts"), dict):
            counts = oheng_summary.get("counts")
        elif isinstance(oheng_summary.get("five"), dict):
            counts = oheng_summary.get("five")

        if isinstance(counts, dict) and dominant_element:
            v = counts.get(dominant_element)
            try:
                fv = float(v) if v is not None else None
            except Exception:
                fv = None

            # 아주 단순한 1차 분류 (정교화는 luck_flow 점수화에서 강화)
            if fv is not None:
                if fv >= 4:
                    structure_type = "과다형"
                elif fv <= 1:
                    structure_type = "약화형"

    comment = {
        "관성": "평가·규칙·조직 구조에서 운이 발동/저지되는 프레임",
        "재성": "돈·성과·결과(수확) 구조에서 운이 발동/저지되는 프레임",
        "식상": "표현·성과·생산(아웃풋) 구조에서 운이 발동/저지되는 프레임",
        "인성": "학습·회복·준비(인풋) 구조에서 운이 발동/저지되는 프레임",
        "비겁": "자기주도·경쟁·동료/형제 구조에서 운이 발동/저지되는 프레임",
    }.get(axis or "", "여러 축이 섞인 혼합 프레임")

    return {
        "name": name,                     # 예: 관성격/재성격/식상격/인성격/비겁격/혼합형
        "axis": axis,                     # 예: 관성/재성/식상/인성/비겁
        "dominant_element": dominant_element,   # 예: 금/수/목/화/토
        "dominant_tengod": dominant_tengod,     # 예: 정관/편관/정재/편재/식신/상관/정인/편인/비견/겁재
        "structure_type": structure_type, # 균형형/과다형/약화형(초기판)
        "commentary": comment,
    }
