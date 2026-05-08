# unteim/engine/report_shinsal_adapter.py
# -*- coding: utf-8 -*-
"""
오행 + 신살 통합 리포트 어댑터
- 오행 불균형 요약 + 신살 해석 요약을 한 번에 묶어 리턴
- 입력: pillars 는 ('간','지') 튜플 또는 {gan,ji} 딕셔너리 (한글/한자 모두 허용)
- 출력: { oheng, shinsal, timeline, card_text }
"""

from __future__ import annotations
from typing import Any, Dict, List, Tuple

# ---- 입력 보정: dict/tuple + 한글 음 → 한자 표준화 --------------------------
_STEM_KO2HZ = {"갑":"甲","을":"乙","병":"丙","정":"丁","무":"戊","기":"己","경":"庚","신":"辛","임":"壬","계":"癸"}
_BRANCH_KO2HZ = {"자":"子","축":"丑","인":"寅","묘":"卯","진":"辰","사":"巳","오":"午","미":"未","신":"申","유":"酉","술":"戌","해":"亥"}

def _to_hanja(x: str) -> str:
    if x in _STEM_KO2HZ:
        return _STEM_KO2HZ[x]
    if x in _BRANCH_KO2HZ:
        return _BRANCH_KO2HZ[x]
    return x  # 이미 한자이거나 기타 표기

def _coerce_pillars(p: Dict[str, Any]) -> Dict[str, Tuple[str, str]]:
    """pillars 를 표준 ('간','지') 한자 튜플로 통일"""
    out: Dict[str, Tuple[str, str]] = {}
    for k, v in p.items():
        if isinstance(v, dict) and "gan" in v and "ji" in v:
            out[k] = (_to_hanja(str(v["gan"])), _to_hanja(str(v["ji"])))
        elif isinstance(v, (list, tuple)) and len(v) == 2:
            out[k] = (_to_hanja(str(v[0])), _to_hanja(str(v[1])))
        else:
            raise ValueError(f"pillars['{k}']는 ('간','지') 튜플 또는 {{gan,ji}} 형태여야 합니다.")
    return out
# ---------------------------------------------------------------------------

# 오행 분석기 로딩 (실제 모듈명이 다르면 여기만 바꾸세요)
try:
    from .oheng_analyzer import analyze_oheng as _analyze_oheng_impl
except Exception:
    def _analyze_oheng_impl(x: Any, *, strict: bool | None = None) -> Dict[str, Any]:
        return {
            "balance": {"목": -1, "화": 1, "토": 0, "금": 0, "수": 0},
            "advice": "목 기운 보완이 필요합니다. 그린·동쪽 계열을 활용하세요.",
        }


def analyze_oheng(pillars: Dict[str, Tuple[str, str]], *, strict: bool | None = None) -> Dict[str, Any]:
    """표준 pillars dict를 ohengAnalyzer 엔트리에 넘기는 얇은 래퍼."""
    return _analyze_oheng_impl(pillars, strict=strict)

# 신살 분석 + 확장 요약
from .shinsal_detector import analyze_shinsal_with_enrichment  # 반드시 존재

def calc_daewoon_periods(_pillars: Dict[str, Tuple[str, str]]) -> List[Tuple[int, int, str]]:
    """대운 구간 [(시작연, 끝연, 라벨), ...]. daewoonCalculator 연동은 추후 교체 가능."""
    return [(2025, 2034, "대운-1"), (2035, 2044, "대운-2")]


def years_for_range(start_year: int, end_year: int) -> List[int]:
    """연도 포함 구간 → 연도 리스트."""
    return list(range(int(start_year), int(end_year) + 1))


# (가중치 룰은 임시 간단 버전 — 필요시 JSON으로 승격)
def _score_hit(name: str) -> int:
    base = {
        "천덕귀인": 3, "문창귀인": 2, "도화": 2, "홍염": 2,
        # 나머지는 1
    }
    # '...살' 접미 제거하여 키 유연화
    key = name.replace("살", "")
    return base.get(key, 1)


def build_oheng_shinsal_report(pillars: Dict[str, Any]) -> Dict[str, Any]:
    """
    pillars 예시(둘 다 허용):
      A) 튜플: {
            "year": ("丙","午"),
            "month": ("庚","子"),
            "day": ("戊","申"),
            "hour": ("癸","丑")
         }
      B) 딕셔너리: {
            "year": {"gan":"병","ji":"오"},
            "month": {"gan":"경","ji":"자"},
            "day": {"gan":"무","ji":"신"},
            "hour": {"gan":"계","ji":"축"}
         }
    """
    # 1) 입력 표준화
    pillars = _coerce_pillars(pillars)

    # 2) 오행/신살 분석
    oheng = analyze_oheng(pillars)
    shinsal = analyze_shinsal_with_enrichment(pillars)

    # 3) 카드용 텍스트
    oheng_text = "오행 균형: " + ", ".join([f"{k}:{v:+d}" for k, v in oheng.get("balance", {}).items()])
    shinsal_text = shinsal["report"]["summary_text"]

    card_text = (
        "🔷 오행 요약\n"
        f"{oheng_text}\n\n"
        "🔶 신살 요약\n"
        f"{shinsal_text}\n\n"
        "🧧 추천 번들(색/방위/아이템)\n"
        f"{shinsal['report']['bundle']}"
    )

    # 4) (간단 훅) 대운·세운 타임라인
    dw_periods = calc_daewoon_periods(pillars)  # [(start,end,label), ...]
    timeline: List[Dict[str, Any]] = []
    for start, end, label in dw_periods:
        years = years_for_range(start, end)
        for y in years:
            hits = []
            for p in ["year", "month", "day", "hour"]:
                for e in shinsal["enriched"]["by_pillar"].get(p, []):
                    hits.append({
                        "name": e["name"],
                        "pillar": p,
                        "score": _score_hit(e["name"])
                    })
            if hits:
                # 연도별 상위 2개만 요약
                top = sorted(hits, key=lambda x: x["score"], reverse=True)[:2]
                timeline.append({"year": y, "bucket": label, "top": top})

    # 5) 결과 패키지
    return {
        "oheng": oheng,
        "shinsal": shinsal,
        "timeline": {"events": timeline},
        "card_text": card_text
    }
