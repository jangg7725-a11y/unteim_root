# unteim/engine/tengods_element_link_v1.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, Any, Optional

# 천간 -> 오행
GAN_TO_ELEM = {
    "갑": "목", "을": "목",
    "병": "화", "정": "화",
    "무": "토", "기": "토",
    "경": "금", "신": "금",
    "임": "수", "계": "수",
}

# 일간 표기가 한자만 올 때 (다른 모듈과 동일하게 보정)
_HANJA_TO_KOR_GAN = {
    "甲": "갑", "乙": "을", "丙": "병", "丁": "정", "戊": "무",
    "己": "기", "庚": "경", "辛": "신", "壬": "임", "癸": "계",
}

# 오행 상생/상극 관계
GEN = {"목": "화", "화": "토", "토": "금", "금": "수", "수": "목"}   # 내가 생하는(식상)
FWD = GEN
REV = {v: k for k, v in GEN.items()}                                # 나를 생하는(인성)
KE = {"목": "토", "토": "수", "수": "화", "화": "금", "금": "목"}    # 내가 극하는(재성)
KED = {v: k for k, v in KE.items()}                                 # 나를 극하는(관성)

def _f(x) -> float:
    try:
        return float(x or 0.0)
    except Exception:
        return 0.0

def _day_element_from_pillars(packed: Dict[str, Any]) -> Optional[str]:
    _p = packed.get("pillars")
    pillars: Dict[str, Any] = _p if isinstance(_p, dict) else {}
    _d = pillars.get("day")
    day: Dict[str, Any] = _d if isinstance(_d, dict) else {}
    raw = str(day.get("gan") or "").strip()
    gan = _HANJA_TO_KOR_GAN.get(raw, raw)
    return GAN_TO_ELEM.get(gan)

def attach_tengods_element_link_v1(packed: Dict[str, Any]) -> None:
    """
    - ten_gods_strength(5축) + five_elements_strength를 이용해
      '왜 관성이 강/약한지'를 오행 관점으로 자동 설명.
    - 결과:
      packed["analysis"]["ten_gods_element_link"]
      packed["analysis"]["ten_gods_reasoning"]
    """
    if not isinstance(packed, dict):
        return
    _an = packed.get("analysis")
    a: Dict[str, Any] = _an if isinstance(_an, dict) else {}
    packed["analysis"] = a

    day_elem = _day_element_from_pillars(packed)
    _fe = a.get("five_elements_strength")
    fe: Dict[str, Any] = _fe if isinstance(_fe, dict) else {}
    _tg = a.get("ten_gods_strength")
    tg: Dict[str, Any] = _tg if isinstance(_tg, dict) else {}
    _tc = a.get("ten_gods_count")
    tg_cnt: Dict[str, Any] = _tc if isinstance(_tc, dict) else {}

    if not day_elem:
        a["ten_gods_element_link"] = {"ok": False, "reason": "day_element_not_found"}
        return

    # 5축이 대응되는 '오행'을 일간 기준으로 결정
    axis_to_elem = {
        "비겁": day_elem,
        "식상": FWD.get(day_elem),
        "인성": REV.get(day_elem),
        "재성": KE.get(day_elem),
        "관성": KED.get(day_elem),
    }

    axis_scores: Dict[str, Dict[str, Any]] = {}
    for axis, elem in axis_to_elem.items():
        axis_scores[axis] = {
            "axis_strength": _f(tg.get(axis)),
            "axis_count": _f(tg_cnt.get(axis)),
            "linked_element": elem,
            "element_strength": _f(fe.get(elem)),
        }

    # 관성 이유 문장 자동 생성(짧고 명확)
    g = axis_scores.get("관성", {})
    elem = g.get("linked_element")
    es = _f(g.get("element_strength"))
    ts = _f(g.get("axis_strength"))

    if elem:
        if es >= 0.7:
            why = f"관성은 일간({day_elem})을 극하는 '{elem}' 기운에서 오는데, 이번 원국/기세에서 '{elem}'이 강하게 잡혀(오행 강도 {es:.2f}) 관성 축이 올라갑니다."
        elif es >= 0.4:
            why = f"관성은 일간({day_elem})을 극하는 '{elem}' 기운에서 나오며, '{elem}'이 중간 이상(오행 강도 {es:.2f})이라 관성 축이 안정적으로 형성됩니다."
        else:
            why = f"관성은 일간({day_elem})을 극하는 '{elem}' 기운에서 나오는데, '{elem}'이 약해(오행 강도 {es:.2f}) 관성 축이 크게 뜨지는 않습니다."
    else:
        why = "관성 축의 연결 오행을 계산하지 못했습니다."

    a["ten_gods_element_link"] = {
        "ok": True,
        "day_element": day_elem,
        "axis_to_element": axis_to_elem,
        "axis_scores": axis_scores,
    }
    a["ten_gods_reasoning"] = {
        "gwanseong_why": why,
        "gwanseong_strength": ts,
        "gwanseong_element_strength": es,
    }
