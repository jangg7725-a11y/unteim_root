# unteim/engine/element_normalizer.py
from __future__ import annotations
from typing import Any

_HANJA_TO_KR = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}
_KR_SET = {"목", "화", "토", "금", "수"}

def norm_elem(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, str):
        if v in _HANJA_TO_KR:
            return _HANJA_TO_KR[v]
        if v in _KR_SET:
            return v
        return v
    return v

def deep_norm(obj: Any) -> Any:
    """dict/list/tuple 안에 있는 모든 문자열 오행(한자)을 한글로 변환"""
    if isinstance(obj, dict):
        return {k: deep_norm(norm_elem(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [deep_norm(norm_elem(x)) for x in obj]
    if isinstance(obj, tuple):
        return tuple(deep_norm(norm_elem(x)) for x in obj)
    # 기본형
    return norm_elem(obj)
