# unteim/engine/hidden_stems.py
# -*- coding: utf-8 -*-
# pyright: reportAttributeAccessIssue=false

"""
지장간(地藏干) 계산

출력 구조(예):
{
  "year":  {"branch":"E", "branch_element":"火", "hiddens":[{"stem":"丙","element":"火","role":"본기","sipsin":"정인"} ...]},
  "month": {...},
  "day":   {...},
  "hour":  {...},
}
"""

from __future__ import annotations

from typing import Dict, List, Any, Tuple

from .oheng import STEM_OHENG, BRANCH_OHENG
from .sipsin import ten_god

# ✅ 지지 -> 지장간(본기/중기/여기) 테이블
# (필요하면 실제 표에 맞춰 조정 가능)
HIDDEN_STEMS_TABLE: Dict[str, List[str]] = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "戊", "庚"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
}

HIDDEN_LABELS = ["본기", "중기", "여기"]


def hidden_stems_for_branch(branch: str) -> List[Dict[str, Any]]:
    """
    branch: 지지 한 글자(예: "子")
    return: [{"stem":..., "element":..., "role":...}, ...]
    """
    stems = HIDDEN_STEMS_TABLE.get(branch, [])
    out: List[Dict[str, Any]] = []
    for i, s in enumerate(stems):
        out.append(
            {
                "stem": s,
                "element": STEM_OHENG.get(s, ""),
                "role": HIDDEN_LABELS[i] if i < len(HIDDEN_LABELS) else "기타",
            }
        )
    return out


def compute_hidden_stems(pillars: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
    """
    pillars 형태:
    {
      "year": {"stem":"甲","branch":"子"},
      "month":{"stem":"...","branch":"..."},
      "day":  {"stem":"...","branch":"..."},
      "hour": {"stem":"...","branch":"..."},
    }
    """
    day_stem = (pillars.get("day") or {}).get("stem", "")

    result: Dict[str, Dict[str, Any]] = {}

    for key, pb in (pillars or {}).items():
        br = (pb or {}).get("branch", "")
        hiddens = hidden_stems_for_branch(br)

        # ✅ 각 지장간에 십신 부여: ten_god(day_stem, target_stem)
        if day_stem:
            for h in hiddens:
                s = h.get("stem", "")
                if s:
                    try:
                        h["sipsin"] = ten_god(day_stem, s)
                    except Exception as e:
                        h["sipsin"] = {
                            "error": "ten_god failed",
                            "detail": f"{type(e).__name__}: {e}",
                        }

        result[key] = {
            "branch": br,
            "branch_element": BRANCH_OHENG.get(br, ""),
            "hiddens": hiddens,
        }

    return result


def _normalize_pillars_branches(pillars: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """year/month/day/hour → {stem, branch} (튜플·dict·gan/ji 모두 허용)."""
    out: Dict[str, Dict[str, str]] = {}
    for k in ("year", "month", "day", "hour"):
        v = (pillars or {}).get(k)
        stem, branch = "", ""
        if isinstance(v, dict):
            stem = str(v.get("stem") or v.get("gan") or "").strip()
            branch = str(v.get("branch") or v.get("ji") or "").strip()
        elif isinstance(v, (tuple, list)) and len(v) >= 2:
            stem, branch = str(v[0] or "").strip(), str(v[1] or "").strip()
        out[k] = {"stem": stem, "branch": branch}
    return out


def _weights_for_hidden_count(n: int) -> List[int]:
    """지장간 개수별 비율(%), 합 100."""
    if n <= 0:
        return []
    if n == 1:
        return [100]
    if n == 2:
        return [60, 40]
    if n == 3:
        return [50, 30, 20]
    base, rem = divmod(100, n)
    return [base + (1 if i < rem else 0) for i in range(n)]


def pillars_hidden_stems(pillars: Dict[str, Any]) -> Dict[str, List[Tuple[str, int]]]:
    """
    기둥별 지장간 (천간, 가중치%) 목록.
    리포트/HTML 등에서 사용 — 가중치는 본기/중기/여기 역할에 따른 단순 비율.
    """
    norm = _normalize_pillars_branches(pillars)
    result: Dict[str, List[Tuple[str, int]]] = {}
    for key in ("year", "month", "day", "hour"):
        br = (norm.get(key) or {}).get("branch", "")
        stems = HIDDEN_STEMS_TABLE.get(br, [])
        wts = _weights_for_hidden_count(len(stems))
        pairs: List[Tuple[str, int]] = []
        for i, s in enumerate(stems):
            wt = wts[i] if i < len(wts) else 0
            pairs.append((s, int(wt)))
        result[key] = pairs
    return result


def count_stem_presence(pillars: Dict[str, Any]) -> Dict[str, int]:
    """네 기둥 지장간 가중치를 천간 글자별로 합산."""
    ph = pillars_hidden_stems(pillars)
    agg: Dict[str, int] = {}
    for key in ("year", "month", "day", "hour"):
        for st, wt in ph.get(key, []):
            if st:
                agg[st] = agg.get(st, 0) + int(wt)
    return agg


def hidden_elements_count_for_pillars(pillars: Any, *, strict: bool | None = None) -> Dict[str, float]:
    """
    지장간 가중치를 천간→오행으로 합산. engine.reporters.make_report / format_hidden_counts 호환.
    """
    from .types import coerce_pillars

    cp = coerce_pillars(pillars, strict=strict)
    stem_w = count_stem_presence(cp.as_dict())
    out: Dict[str, float] = {"木": 0.0, "火": 0.0, "土": 0.0, "金": 0.0, "水": 0.0}
    for stem, w in stem_w.items():
        elem = STEM_OHENG.get(stem, "")
        if elem in out:
            out[elem] += float(w)
    return out
