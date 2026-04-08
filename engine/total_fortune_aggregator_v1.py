# unteim/engine/total_fortune_aggregator_v1.py
# -*- coding: utf-8 -*-
"""
총운(통합) 합성 모듈 v1

원칙:
- 계산은 engine에서 분리되어 올라온 report dict를 입력으로 받는다.
- 출력 직전에 '총운 블록'만 통합 합성한다.
- 신살/삼재는 단독해석 금지: 강조/보정 플래그로만 취급한다.
- 용/희/기신은 십신/운 해석의 방향키로만 적용한다.

출력:
report["extra"]["total_fortune"] 에 들어갈 dict 반환
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from engine.samjae_engine_v1 import build_samjae_bundle_v2

def _safe_get(d: Any, path: str, default=None):
    cur = d
    for key in path.split("."):
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def _ensure_path(d: Dict[str, Any], path: str) -> Dict[str, Any]:
    """
    path 예: "extra.total_fortune"
    - 중간 dict 없으면 생성
    - 마지막 dict를 반환
    """
    cur = d
    parts = path.split(".")
    for p in parts:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    return cur


def _as_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def _pick_core_inputs(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    full_analyzer 결과(report)에서 총운 합성에 필요한 핵심 입력만 묶어준다.
    (존재 키가 달라도 안전하게 흡수)
    """
    return {
        "birth_str": report.get("birth_str") or report.get("birth") or "",
        "pillars": report.get("pillars") or {},
        "analysis": report.get("analysis") or {},
        "when": report.get("when") or {},
        # 자주 등장하는 후보 키들을 넓게 수용
        "ohang": (
            _safe_get(report, "analysis.ohang")
            or _safe_get(report, "analysis.five_elements")
            or _safe_get(report, "analysis.elements")
            or {}
        ),
        "yong_hee_gi": (
            _safe_get(report, "analysis.yong_hee_gi")
            or _safe_get(report, "analysis.yongshin")
            or _safe_get(report, "analysis.yong_hee_gi_shin")
            or {}
        ),
        "ten_gods": (
            _safe_get(report, "analysis.ten_gods_strength")
            or _safe_get(report, "analysis.ten_gods")
            or {}
        ),
        "daeun": (
            _safe_get(report, "analysis.daeun")
            or _safe_get(report, "analysis.big_luck")
            or {}
        ),
        "twelve_states": (
            _safe_get(report, "analysis.twelve_states")
            or _safe_get(report, "analysis.12_states")
            or {}
        ),
        "hyung_chung_hap": (
            _safe_get(report, "analysis.hyung_chung_hap")
            or _safe_get(report, "analysis.hch")
            or {}
        ),
        "gongmang": (
            _safe_get(report, "analysis.gongmang")
            or _safe_get(report, "analysis.empty")
            or {}
        ),
        "sinsal": (
            _safe_get(report, "analysis.sinsal")
            or _safe_get(report, "analysis.shinsal")
            or {}
        ),
    }


def _build_personality_block(core: Dict[str, Any]) -> Dict[str, Any]:
    """
    총운: 타고난 성격(요약/키울 점/절제할 점) 블록
    - v1에서는 '자리'를 고정하고, 기존 해석 텍스트가 있으면 가져온다.
    """
    analysis = core.get("analysis") or {}
    # 후보 텍스트 키들(있으면 활용)
    innate = (
        _safe_get(analysis, "personality.innate")
        or _safe_get(analysis, "innate_personality")
        or _safe_get(analysis, "summary.personality")
        or ""
    )
    up = (
        _safe_get(analysis, "personality.up")
        or _safe_get(analysis, "up_points")
        or _safe_get(analysis, "summary.up")
        or ""
    )
    down = (
        _safe_get(analysis, "personality.down")
        or _safe_get(analysis, "down_points")
        or _safe_get(analysis, "summary.down")
        or ""
    )

    # 텍스트가 없으면, 최소 구조만 반환
    return {
        "innate": innate,
        "up": up,
        "down": down,
    }


def _build_timing_blocks(core: Dict[str, Any]) -> Dict[str, Any]:
    """
    총운: 직업/직장, 인연/결혼, 문서/재물, 리스크(사고/질병/사기/승진 등)
    - v1에서는 '자리' 고정 + 기존 키 존재 시 흡수.
    """
    analysis = core.get("analysis") or {}

    def pick(*paths: str) -> str:
        for p in paths:
            v = _safe_get(analysis, p)
            if isinstance(v, str) and v.strip():
                return v
        return ""

    return {
        "career": pick("total.career", "summary.career", "career.commentary"),
        "relationship": pick("total.relationship", "summary.relationship", "relationship.commentary"),
        "wealth_docs": pick("total.wealth_docs", "summary.wealth", "wealth.commentary"),
        "risks": pick("total.risks", "summary.risks", "risks.commentary"),
    }


# --- 삼재/복삼재(자리만 고정) -------------------------------------------
def _samjae_placeholder(core: Dict[str, Any]) -> Dict[str, Any]:
    """
    v1: 아직 삼재 계산기를 붙이기 전 단계.
    - 출력 스키마만 고정해둔다.
    """
    return {
        "enabled": True,
        "is_samjae": None,          # True/False 로 추후 확정
        "stage": None,              # "일반" | "완화" | "전환"
        "year_range": [],           # [2026, 2027, 2028] 같은 형태
        "notes": "v1 placeholder: samjae engine not attached yet",
        "bok_samjae": None,         # True/False (전환 조건 충족 시 True)
    }


# --- 점수(자리만 고정) ---------------------------------------------------
def _score_placeholder(core: Dict[str, Any]) -> Dict[str, Any]:
    """
    v1: 아직 점수 엔진 미연결.
    - 출력 스키마만 고정해둔다.
    """
    return {
        "enabled": True,
        "total_score": None,  # 0~100
        "grade": None,        # "상/중/하" 또는 "A/B/C" 등
        "risk_flags": [],
        "opportunity_flags": [],
        "notes": "v1 placeholder: score engine not attached yet",
    }

def build_total_fortune_block(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    총운 통합 블록 생성
    - personality/timing은 core로 계산
    - samjae는 반드시 pillars가 있는 원본 report로 계산
    """
    core = _pick_core_inputs(report)

    # ✅ samjae는 pillars가 있는 dict로만 계산
    samjae_input = report
    if not isinstance(samjae_input.get("pillars"), dict):
        # 혹시 축약 dict가 들어오면, 최대한 원본 형태로 복구 시도
        cand = report.get("extra", {}).get("_packed")
        if isinstance(cand, dict):
            samjae_input = cand

    out: Dict[str, Any] = {
        "version": "total_fortune_v1",
        "birth_str": report.get("birth_str", ""),
        "when": report.get("when", {}),
        "personality": _build_personality_block(core),
        "timing": _build_timing_blocks(core),

        # 🔥 핵심: samjae는 pillars가 있는 dict로 호출
        "samjae": build_samjae_bundle_v2(samjae_input),

        "flags": {
            "sinsal": report.get("analysis", {}).get("sinsal", {}) or {},
            "gongmang": report.get("analysis", {}).get("gongmang", {}) or {},
        },

        "score": _score_placeholder(core),
    }

    return out

    


def enrich_report_with_total_fortune(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    report["extra"]["total_fortune"] 를 채워 넣는다.
    - 기존 extra가 없으면 생성
    - 이미 값이 있으면 덮어쓴다(현재 단계에서는 항상 최신 합성 우선)
    """
    extra = _ensure_path(report, "extra")
    extra["total_fortune"] = build_total_fortune_block(report)
    return report