# unteim/engine/samjae_engine_v1.py
# -*- coding: utf-8 -*-

from __future__ import annotations
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# 삼재 그룹 정의 (년지 기준)
SAMJAE_GROUPS = {
    "신자진": ["申", "子", "辰"],
    "해묘미": ["亥", "卯", "未"],
    "인오술": ["寅", "午", "戌"],
    "사유축": ["巳", "酉", "丑"],
}

# 각 그룹의 삼재 시작 지지 (통상: 인/사/신/해)
# → 세운 년지가 이 지지일 때 **눌삼재(본삼재)**. 직전 년지=들삼재, 직후 년지=날삼재.
SAMJAE_START = {
    "신자진": "寅",
    "해묘미": "巳",
    "인오술": "申",
    "사유축": "亥",
}

# 12지 순환 (양력 세운 년지 판정용)
_ZHI12 = tuple("子丑寅卯辰巳午未申酉戌亥")


def _zhi_index(ji: str) -> Optional[int]:
    if not ji or len(ji) < 1:
        return None
    c = ji.strip()[0]
    try:
        return _ZHI12.index(c)
    except ValueError:
        return None


def _prev_next_branches(pivot: str) -> Tuple[Optional[str], Optional[str]]:
    """pivot의 직전·직후 지지 (12지 원형)."""
    i = _zhi_index(pivot)
    if i is None:
        return None, None
    return _ZHI12[(i - 1) % 12], _ZHI12[(i + 1) % 12]


def _branch_from_any(x: Any) -> Optional[str]:
    """
    다양한 타입에서 '지지' 1글자를 뽑는다.
    지원:
    - "庚午" 같은 2글자 문자열 -> 2번째 글자
    - dict: {"branch": "..."} / {"ji": "..."} / {"z": "..."} 등
    - 객체(GanJi 등): .branch / .ji / .z 속성
    - 객체(GanJi 등): .gan + .ji 조합이 있으면 ji 사용
    """
    if x is None:
        return None

    # 문자열: "경오", "庚午" 등
    if isinstance(x, str):
        s = x.strip()
        if len(s) >= 2:
            return s[1]
        return None

    # dict
    if isinstance(x, dict):
        for k in ("branch", "ji", "z", "地支"):
            v = x.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()[0]
        for k in ("ganji", "gz", "value", "pillar"):
            v = x.get(k)
            b = _branch_from_any(v)
            if b:
                return b
        return None

    # 객체 속성
    for attr in ("branch", "ji", "z"):
        v = getattr(x, attr, None)
        if isinstance(v, str) and v.strip():
            return v.strip()[0]

    # 객체: gan/ji 조합
    ji = getattr(x, "ji", None)
    if isinstance(ji, str) and ji.strip():
        return ji.strip()[0]

    return None


def _find_group(year_branch: str) -> Optional[str]:
    for group, members in SAMJAE_GROUPS.items():
        if year_branch in members:
            return group
    return None


def _extract_year_branch(packed: Dict[str, Any]) -> Optional[str]:
    # ✅ pillars 위치를 여러 후보에서 찾는다
    pillars = packed.get("pillars")
    if not isinstance(pillars, dict):
        an = packed.get("analysis")
        pillars = an.get("pillars") if isinstance(an, dict) else None
    if not isinstance(pillars, dict):
        inp = packed.get("input")
        pillars = inp.get("pillars") if isinstance(inp, dict) else None
    if not isinstance(pillars, dict):
        ex = packed.get("extra")
        pillars = ex.get("pillars") if isinstance(ex, dict) else None

    if not isinstance(pillars, dict):
        return None

    year_val = pillars.get("year")

    # 1) dict 구조 {'gan': '己', 'ji': '巳'}
    if isinstance(year_val, dict):
        ji = year_val.get("ji")
        if isinstance(ji, str) and ji.strip():
            return ji.strip()

    # 2) 문자열 구조 "己巳"
    if isinstance(year_val, str) and len(year_val) >= 2:
        return year_val[1]

    # 3) 객체 구조 (GanJi 등)
    ji = getattr(year_val, "ji", None)
    if isinstance(ji, str) and ji.strip():
        return ji.strip()

    return None


def _extract_current_sewun_branch(packed: Dict[str, Any]) -> Optional[str]:
    """
    packed에서 'target_year(=meta.year)'에 해당하는 세운 항목을 찾아
    year_pillar의 지지를 반환한다.
    - sewun 리스트 위치: root / analysis 모두 대응
    - item 형태: dict / object 모두 대응
    - year 키: year/start_year/y/from_year 등 최대한 흡수
    """
    # 1) target_year 결정 (meta.year 우선)
    _meta_raw = packed.get("meta")
    meta: Dict[str, Any] = _meta_raw if isinstance(_meta_raw, dict) else {}
    target_year = meta.get("year")
    try:
        target_year = int(target_year) if target_year is not None else datetime.now().year
    except Exception:
        target_year = datetime.now().year

    # 2) sewun list 후보(루트/analysis 모두)
    _an_raw = packed.get("analysis")
    analysis: Dict[str, Any] = _an_raw if isinstance(_an_raw, dict) else {}
    sewun_list = (
        packed.get("sewun")
        or packed.get("sewoon")
        or analysis.get("sewun")
        or analysis.get("sewoon")
        or analysis.get("sewun_list")
        or analysis.get("sewoon_list")
        or []
    )
    if not isinstance(sewun_list, list) or not sewun_list:
        return None

    # 3) item에서 year / year_pillar 뽑는 헬퍼
    def _get_year(it: Any) -> Optional[int]:
        cand = None
        if isinstance(it, dict):
            cand = (
                it.get("year")
                or it.get("start_year")
                or it.get("y")
                or it.get("from_year")
                or it.get("yyyy")
            )
        else:
            cand = (
                getattr(it, "year", None)
                or getattr(it, "start_year", None)
                or getattr(it, "y", None)
                or getattr(it, "from_year", None)
                or getattr(it, "yyyy", None)
            )
        try:
            return int(cand) if cand is not None else None
        except Exception:
            return None

    def _get_year_pillar(it: Any) -> Any:
        if isinstance(it, dict):
            return it.get("year_pillar") or it.get("pillar") or it.get("ganji") or it.get("ganzhi")
        return (
            getattr(it, "year_pillar", None)
            or getattr(it, "pillar", None)
            or getattr(it, "ganji", None)
            or getattr(it, "ganzhi", None)
        )
    
    # 4) target_year 매칭
    for item in sewun_list:
        y = _get_year(item)
        if y == target_year:
            yp = _get_year_pillar(item)
            return _branch_from_any(yp)

    # 5) 못 찾으면 None
    return None


def build_samjae_result(packed: Dict[str, Any]) -> Dict[str, Any]:
    """
    삼재 결과 dict 반환.
    - 들/눌/날: 세운 지지가 눌(본삼재)의 직전·일치·직후이면 각각 들삼재·눌삼재·날삼재.
    - 실패해도 reason / 중간값을 항상 담아 디버깅 가능하게 한다.
    """

    year_branch = _extract_year_branch(packed)
    current_branch = _extract_current_sewun_branch(packed)

    # 기본 결과(항상 필드 유지)
    out: Dict[str, Any] = {
        "enabled": True,
        "year_branch": year_branch,
        "current_sewun_branch": current_branch,
        "group": None,
        "samjae_start_branch": None,
        "is_samjae": False,
        "stage": None,          # "들삼재" | "눌삼재" | "날삼재" — 삼재 구간일 때만
        "stage_code": None,    # "deul" | "nul" | "nal" — API/프론트 분기용
        "bok_samjae": False,
        "reason": None,
    }

    if not year_branch:
        out["enabled"] = False
        out["reason"] = "year_branch_not_found"
        return out

    group = _find_group(year_branch)
    if not group:
        out["enabled"] = False
        out["reason"] = "year_branch_not_in_groups"
        return out

    pivot = SAMJAE_START.get(group)
    out["group"] = group
    out["samjae_start_branch"] = pivot

    if not pivot:
        out["enabled"] = False
        out["reason"] = "samjae_pivot_missing"
        return out

    if not current_branch:
        out["enabled"] = False
        out["reason"] = "current_sewun_branch_not_found"
        return out

    deul_br, nal_br = _prev_next_branches(pivot)
    if not deul_br or not nal_br:
        out["enabled"] = False
        out["reason"] = "branch_cycle_error"
        return out

    # 세운 지지 정규화 (한 글자)
    cur = current_branch.strip()[0] if current_branch else ""

    if cur == deul_br:
        out["is_samjae"] = True
        out["stage"] = "들삼재"
        out["stage_code"] = "deul"
    elif cur == pivot:
        out["is_samjae"] = True
        out["stage"] = "눌삼재"
        out["stage_code"] = "nul"
    elif cur == nal_br:
        out["is_samjae"] = True
        out["stage"] = "날삼재"
        out["stage_code"] = "nal"
    else:
        out["is_samjae"] = False
        out["stage"] = None
        out["stage_code"] = None

    return out

# ============================================================
# 🔥 v2 확장: D옵션 (년지 + 대운 + sewun 교차) 복삼재 판정
# ============================================================

def _detect_cross_flags(packed: Dict[str, Any]) -> Dict[str, bool]:
    """
    다른 엔진에서 계산된 플래그를 최대한 안전하게 읽는다.
    없으면 False 처리 (기존 구조 절대 안 깨짐)
    """
    flags_raw = packed.get("flags")
    if not isinstance(flags_raw, dict):
        flags_raw = {}
    an = packed.get("analysis")
    flags_an = an.get("flags", {}) if isinstance(an, dict) else {}
    flags: Dict[str, Any] = flags_raw or (flags_an if isinstance(flags_an, dict) else {})

    return {
        "yong_sewun": bool(flags.get("is_yongshin_sewun")),
        "yong_daewun": bool(flags.get("is_yongshin_daewun")),
        "gishin_sewun": bool(flags.get("is_gishin_sewun")),
        "gishin_daewun": bool(flags.get("is_gishin_daewun")),
        "supportive_hap": bool(flags.get("has_supportive_hap")),
        "harmful_chung": bool(flags.get("has_harmful_chung")),
    }


def _stage_to_bundle_phase(stage: Optional[str]) -> str:
    """들삼재/눌삼재/날삼재 → build_samjae_bundle_v2 가중치 키(입력/눌림/끝)."""
    if not stage:
        return "눌림"
    s = str(stage)
    if "들" in s:
        return "입력"
    if "날" in s:
        return "끝"
    if "눌" in s:
        return "눌림"
    return "눌림"


def build_samjae_bundle_v2(packed: Dict[str, Any]) -> Dict[str, Any]:
    """
    기존 build_samjae_result() 결과를 기반으로
    삼재 / 완화삼재 / 전환삼재(복삼재) 판정까지 확장
    """

    base = build_samjae_result(packed)

    # 삼재 아니면 그대로 반환
    if not base.get("is_samjae"):
        base.update({
            "mode": "NONE",
            "risk_level": 0,
            "relief_score": 0,
            "risk_score": 0,
        })
        return base

    phase = base.get("stage")
    phase_key = _stage_to_bundle_phase(phase if isinstance(phase, str) else None)
    cross = _detect_cross_flags(packed)

    relief_score = 0
    risk_score = 0
    reasons = []

    # ----------------------------
    # 🔹 용신 교차 (완화/전환 요소)
    # ----------------------------
    if cross["yong_sewun"]:
        relief_score += 1
        reasons.append("sewun 용신(+1)")
    if cross["yong_daewun"]:
        relief_score += 1
        reasons.append("대운 용신(+1)")
    if cross["supportive_hap"]:
        relief_score += 1
        reasons.append("형합 완화(+1)")

    # ----------------------------
    # 🔹 기신 / 충 요소 (리스크 강화)
    # ----------------------------
    if cross["gishin_sewun"]:
        risk_score += 1
        reasons.append("sewun 기신(+1)")
    if cross["gishin_daewun"]:
        risk_score += 1
        reasons.append("대운 기신(+1)")
    if cross["harmful_chung"]:
        risk_score += 1
        reasons.append("충/파/해(+1)")

    # ----------------------------
    # 🔹 기본 위험도 (들=입력 / 눌=눌림 / 날=끝)
    # ----------------------------
    phase_weight = {
        "입력": 3,     # 들삼재
        "눌림": 2,     # 눌삼재
        "끝": 1        # 날삼재
    }.get(phase_key, 2)

    risk_level = phase_weight

    if risk_score >= 2:
        risk_level += 1
    if relief_score >= 2:
        risk_level -= 1

    risk_level = max(1, min(risk_level, 3))

    # ----------------------------
    # 🔹 모드 판정
    # ----------------------------
    if relief_score >= 2 and risk_score <= 1:
        mode = "TRANSFORM"   # 복삼재
    elif relief_score >= 1:
        mode = "MITIGATED"   # 완화삼재
    else:
        mode = "NORMAL"      # 일반삼재

    base.update({
        "mode": mode,
        "risk_level": risk_level,
        "relief_score": relief_score,
        "risk_score": risk_score,
        "reasons": reasons,
    })

    return base   