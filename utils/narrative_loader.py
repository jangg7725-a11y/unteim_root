# utils/narrative_loader.py
# -*- coding: utf-8 -*-
"""
외부 narrative/*.json 에서 문장을 로드합니다.
코드 수정 없이 JSON만 편집하면 리포트 문구를 변경할 수 있습니다.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

_ROOT = Path(__file__).resolve().parent.parent
_NARRATIVE_DIR = _ROOT / "narrative"

# file_stem -> parsed dict
_CACHE: Dict[str, Dict[str, Any]] = {}


def narrative_dir() -> Path:
    return _NARRATIVE_DIR


def _resolve_path(file_name: str) -> Path:
    name = file_name.strip()
    if not name.endswith(".json"):
        name = f"{name}.json"
    return _NARRATIVE_DIR / name


def load_sentences(file_name: str) -> Dict[str, Any]:
    """
    JSON 파일 전체를 dict로 로드합니다. (확장자 생략 가능)
    동일 파일은 프로세스 내 캐시됩니다.
    """
    stem = file_name.replace(".json", "").strip()
    if stem in _CACHE:
        return _CACHE[stem]

    path = _resolve_path(file_name)
    if not path.is_file():
        _CACHE[stem] = {}
        return _CACHE[stem]

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        data = {}
    _CACHE[stem] = data
    return _CACHE[stem]


def clear_narrative_cache() -> None:
    """테스트용: 캐시 초기화"""
    _CACHE.clear()


def _get_by_path(data: Any, path: str) -> Any:
    cur: Any = data
    for part in path.split("."):
        if part == "":
            continue
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def get_value(file_name: str, key: str, default: Any = None) -> Any:
    """
    점(.) 경로로 중첩 키 조회. 예: 'summary.templates.dom_weak'
    """
    data = load_sentences(file_name)
    v = _get_by_path(data, key)
    return default if v is None else v


def get_sentence(file_name: str, key: str, default: str = "") -> str:
    """
    key에 해당하는 값을 문자열로 반환.
    - 값이 str이면 그대로
    - 값이 list이면 첫 번째 요소(또는 default)
    """
    v = get_value(file_name, key, None)
    if isinstance(v, str):
        return v
    if isinstance(v, list) and v:
        el = v[0]
        return str(el) if el is not None else default
    if v is not None and not isinstance(v, (dict, list)):
        return str(v)
    return default


def get_list(file_name: str, key: str, default: Optional[List[str]] = None) -> List[str]:
    """키가 문자열 리스트일 때 사용"""
    v = get_value(file_name, key, None)
    if isinstance(v, list):
        return [str(x) for x in v if _as_nonempty_str(x)]
    if default is not None:
        return default
    return []


def _as_nonempty_str(x: Any) -> bool:
    return isinstance(x, str) and bool(x.strip())


def list_keys_flat(
    file_name: str, prefix: str = ""
) -> List[str]:
    """디버깅용: 최상위 키 나열"""
    data = load_sentences(file_name)
    if not isinstance(data, dict):
        return []
    keys = list(data.keys())
    if prefix:
        keys = [k for k in keys if str(k).startswith(prefix)]
    return keys
