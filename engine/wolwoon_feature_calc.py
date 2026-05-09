# unteim/engine/wolwoon_feature_calc.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from .wolwoon_patterns import PATTERN_META
from engine.hap_chung_interpreter import get_relation_pattern_slots as _get_relation_slots

# -----------------------------
# 0) 관계/충합 기본 테이블 (엔진용 최소셋)
# -----------------------------
CHUNG = {
    ("자", "오"), ("오", "자"),
    ("축", "미"), ("미", "축"),
    ("인", "신"), ("신", "인"),
    ("묘", "유"), ("유", "묘"),
    ("진", "술"), ("술", "진"),
    ("사", "해"), ("해", "사"),
}
HAP = {
    ("자", "축"), ("축", "자"),
    ("인", "해"), ("해", "인"),
    ("묘", "술"), ("술", "묘"),
    ("진", "유"), ("유", "진"),
    ("사", "신"), ("신", "사"),
    ("오", "미"), ("미", "오"),
}

# 형/파는 너희 엔진에 이미 표가 있으면 거기 연결하는 게 정답이라,
# 여기서는 "있는 경우만 가산"용 최소 틀만 둠(없으면 0점)
HYEONG: set[Tuple[str, str]] = set()
PA: set[Tuple[str, str]] = set()

# -----------------------------
# 1) 점수 규칙(고정) - 너와 합의한 기준
# -----------------------------
def _unseong_adj(stage: str | None) -> int:
    if not stage:
        return 0
    # 발현
    if stage in ("장생", "관대", "건록", "제왕"):
        return 15
    # 불안
    if stage in ("쇠", "병", "사"):
        return 5
    # 소멸
    if stage in ("묘", "절", "태", "양"):
        return -15
    return 0

def _oheng_adj(oheng_summary: Dict[str, Any] | None) -> int:
    """
    oheng_summary 예시(권장):
      {
        "yongshin_ok": True/False,
        "yongshin_level": "strong"/"normal"/"weak",
        "gishin_level": "strong"/"normal"/"weak"
      }
    없으면 0점 반환.
    """
    if not oheng_summary:
        return 0
    if oheng_summary.get("yongshin_level") == "strong":
        return 20
    if oheng_summary.get("yongshin_level") == "normal":
        return 10
    if oheng_summary.get("gishin_level") == "strong":
        return -20
    if oheng_summary.get("gishin_level") == "normal":
        return -10
    return 0

def _gongmang_penalty(is_gongmang: bool, trigger_power: int, has_hap: bool) -> int:
    if not is_gongmang:
        return 0
    # 공망 + 충이면 -25, 공망+합이면 -30, 그냥 공망이면 -40
    if trigger_power >= 15:
        return -25
    if has_hap:
        return -30
    return -40


# -----------------------------
# 2) 십신/신살 점수: "입력으로 받은 신호"를 점수로 바꿈
#    (즉, ten_god 계산 자체는 엔진 기존 모듈을 쓰고,
#     여기서는 '이미 계산된 결과'를 받아 점수화만 함)
# -----------------------------
def _ten_score(signal: Dict[str, Any], pattern_id: str) -> int:
    """
    signal 예시:
      {
        "hit_main": True/False,
        "hit_sub": True/False,
        "hit_conflict": True/False,
      }
    """
    if signal.get("hit_conflict"):
        return -20
    if signal.get("hit_main"):
        return 30
    if signal.get("hit_sub"):
        return 15
    return 0

def _shinsal_score(signal: Dict[str, Any], pattern_id: str) -> int:
    """
    signal 예시:
      {
        "core": ["천을", "문창", ...],
        "sub": ["천덕", ...],
        "bad": ["백호", "겁살", ...],
      }
    """
    core = signal.get("core") or []
    sub = signal.get("sub") or []
    bad = signal.get("bad") or []
    return (10 * len(core)) + (5 * len(sub)) - (10 * len(bad))


# -----------------------------
# 3) 충합/트리거 계산: 월지 vs 원국 지지들
# -----------------------------
def _clash_hap_from_branches(month_branch: str, natal_branches: List[str]) -> Dict[str, int]:
    trigger_power = 0
    clash_hap_score = 0
    has_hap = False

    for b in natal_branches:
        if (month_branch, b) in CHUNG:
            trigger_power = max(trigger_power, 15)
            clash_hap_score += 15
        elif (month_branch, b) in HAP:
            has_hap = True
            trigger_power = max(trigger_power, 10)
            clash_hap_score += 10
        elif (month_branch, b) in HYEONG:
            trigger_power = max(trigger_power, 8)
            clash_hap_score += 8
        elif (month_branch, b) in PA:
            trigger_power = max(trigger_power, 8)
            clash_hap_score += 8

    return {
        "trigger_power": trigger_power,
        "clash_hap_score": clash_hap_score,
        "has_hap": 1 if has_hap else 0,
    }


# -----------------------------
# 4) features_by_pattern 생성 메인
# -----------------------------
def build_features_by_pattern(
    *,
    pattern_signals: Dict[str, Dict[str, Any]],
    month_branch: str,
    natal_branches: List[str],
    unseong_stage: str | None,
    oheng_summary: Dict[str, Any] | None,
    is_gongmang: bool,
) -> Dict[str, Dict[str, Any]]:
    """
    pattern_signals: 패턴별로 십신/신살 hit 여부를 이미 계산해둔 결과
      {
        "exam_pass": {
           "ten": {"hit_main": True, "hit_sub": False, "hit_conflict": False},
           "shinsal": {"core": ["문창"], "sub": [], "bad": []},
        },
        ...
      }
    month_branch: 이번 달 월지(예: "인","묘"...)
    natal_branches: 원국 지지 리스트(년/월/일/시 지지) 예: ["오","자","신","축"]
    unseong_stage: 이번 달에 해당 사건축(관성/재성 등)에 대한 운성 결과(없으면 None)
    oheng_summary: 오행 보정 입력(없으면 None)
    is_gongmang: 이번 달 월지/핵심축이 공망이면 True

    반환:
      features_by_pattern[pattern_id] = {
         ten_score, shinsal_score, clash_hap_score, trigger_power,
         oheng_adj, unseong_adj, gongmang_penalty
      }
    """
    rel = _clash_hap_from_branches(month_branch, natal_branches)
    trigger_power = int(rel["trigger_power"])
    clash_hap_score = int(rel["clash_hap_score"])
    has_hap = bool(rel["has_hap"])

    oh_adj = _oheng_adj(oheng_summary)
    un_adj = _unseong_adj(unseong_stage)
    gm_pen = _gongmang_penalty(is_gongmang, trigger_power, has_hap)

    out: Dict[str, Dict[str, Any]] = {}

    for pid in PATTERN_META.keys():
        sig = pattern_signals.get(pid, {})
        ten_sig = sig.get("ten") or {}
        sh_sig = sig.get("shinsal") or {}

        features = {
            "ten_score": _ten_score(ten_sig, pid),
            "shinsal_score": _shinsal_score(sh_sig, pid),
            "clash_hap_score": clash_hap_score,
            "trigger_power": trigger_power,
            "oheng_adj": oh_adj,
            "unseong_adj": un_adj,
            "gongmang_penalty": gm_pen,
        }
        try:
            _relation = _get_relation_slots({"wolwoon": {"features": features}})
            if _relation["found"]:
                features["relation_slots"] = _relation
        except Exception:
            pass
        out[pid] = features

    return out
