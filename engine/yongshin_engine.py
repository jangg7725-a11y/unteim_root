# unteim/engine/yongshin_engine.py
from __future__ import annotations
from typing import Any, Dict, Optional

_HANJA_TO_KR = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}
_KR_TO_KR = {"목": "목", "화": "화", "토": "토", "금": "금", "수": "수"}

def _norm_elem(e):
    if not e:
        return None
    return _HANJA_TO_KR.get(e, _KR_TO_KR.get(e, e))

# 오행 상생(생) 관계: 부모 -> 자식
# 목->화->토->금->수->목
_GENERATES = {"목": "화", "화": "토", "토": "금", "금": "수", "수": "목"}
# 오행 상극(극) 관계: A가 B를 극한다
# 목극토, 토극수, 수극화, 화극금, 금극목
_CONTROLS = {"목": "토", "토": "수", "수": "화", "화": "금", "금": "목"}

# 격국 축 → 용신 방향(오행) — 모듈 상수로 두어 스코프/미정의 린트 방지
_AXIS_TO_YONG: Dict[str, str] = {
    "관성": "수",
    "재성": "금",
    "식상": "토",
    "인성": "목",
    "비겁": "토",
}


def _pick_lowest_element(oheng: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    oheng 요약에서 가장 약한 오행(보완 우선)을 추정.
    기대 키 예:
      - oheng["counts"] = {"목":x,"화":y,"토":z,"금":k,"수":m}
      - 또는 oheng["five"] = {...}
    """
    if not isinstance(oheng, dict):
        return None

    counts = None
    if isinstance(oheng.get("counts"), dict):
        counts = oheng.get("counts")
    elif isinstance(oheng.get("five"), dict):
        counts = oheng.get("five")

    if not isinstance(counts, dict) or not counts:
        return None

    # 숫자 비교 가능한 것만
    best = None
    best_v = None
    for k, v in counts.items():
        try:
            fv = float(v)
        except Exception:
            continue
        if best_v is None or fv < best_v:
            best_v = fv
            best = k
    return best


def analyze_yongshin_axis(
    *,
    geukguk: Optional[Dict[str, Any]] = None,
    oheng: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    운트임 최소 안정판 용신/희신/기신 산출.

    원칙:
    - geukguk.axis를 우선 사용 (관성/재성/식상/인성/비겁)
    - axis 기반 기본 용신 방향을 정하고,
    - oheng에서 부족 오행이 있으면 우선순위에 반영(보완 현실성)
    """
    axis = None
    if isinstance(geukguk, dict):
        axis = geukguk.get("axis")

    # 1) axis 기반 기본 용신 후보 — _AXIS_TO_YONG 참고
    ax_key = str(axis).strip() if axis is not None else ""
    yong = _AXIS_TO_YONG.get(ax_key) if ax_key else None

    # 2) oheng 부족 오행이 뚜렷하면 용신을 그쪽으로 조정(현실 체감 강화)
    low = _pick_lowest_element(oheng)
    # low가 있으면 yong을 low로 우선 덮는 방식은 과격할 수 있어
    # => "용신이 없거나 axis가 None"일 때만 low를 채택
    if yong is None and low:
        yong = low

    # 한자(木·火…) → 한글(목·화…) 통일 후 희신/기신 계산 (_GENERATES 키와 맞춤)
    yong = _norm_elem(yong)

    # 3) 희신(heesin): 용신을 생(生)해주는 오행
    hee = None
    if yong:
        for parent, child in _GENERATES.items():
            if child == yong:
                hee = parent
                break

    # 4) 기신(gisin): 용신을 극(剋)하는 오행 (리스크)
    gi = None
    if yong:
        for attacker, target in _CONTROLS.items():
            if target == yong:
                gi = attacker
                break

    hee = _norm_elem(hee)
    gi = _norm_elem(gi)

    # 5) 설명문(짧고 명확하게)
    y_reason = f"격국 축({axis}) 기반 보완 방향" if axis else "격국 축이 불명확하여 오행 균형 중심으로 보완"
    if low and (axis is None):
        y_reason += f" / 오행 부족({low}) 보완 우선"


    return {
        "yongshin": {"element": yong, "reason": y_reason},
        "heesin": {"element": hee, "reason": "용신을 생(生)하는 보조 기운" if hee else "보조 기운 판정 보류"},
        "gisin": {"element": gi, "reason": "용신을 극(剋)하는 리스크 기운" if gi else "리스크 기운 판정 보류"},
    }
