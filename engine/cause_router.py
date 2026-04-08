# -*- coding: utf-8 -*-
"""
cause_router.py
- (오행 + 십신 + 12운성 + 신살) -> 상담가톤 원인/조언 문장 생성 라우터
- test_shinsal.py에서 바로 호출 가능
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple

# 기존 문장 생성기(오슈님이 붙여넣은 것)
from .cause_sentence_engine import build_consult_sentence


# -----------------------------
# 0) 기본 분류(사람/재물/건강/사건)
# -----------------------------
# 필요하면 계속 확장하세요.
DOMAIN_BY_SHINSAL: Dict[str, str] = {
    "천을귀인": "people",
    "도화": "people",
    "역마살": "event",
    "겁살": "money",
    "재살": "event",
    "망신살": "people",
    "월살": "event",
    "지살": "event",
    "천살": "event",
    "화개살": "mind",
    "괴강살": "people",
    "백호살": "health",
    "수옥살": "event",
}

# 12운성은 별도 처리
def _is_lifestage(name: str) -> bool:
    return name.startswith("12운성:")

def _extract_lifestage(name: str) -> str:
    # "12운성:長生" -> "長生"
    return name.split(":", 1)[1] if ":" in name else name


# -----------------------------
# 1) 오행 연결(임시 기본값)
# -----------------------------
# TODO: 오행 엔진 붙이면 아래 함수만 교체하면 됩니다.
def infer_element_context(pillars: Dict[str, Tuple[str, str]]) -> Dict[str, str]:
    """
    return 예:
      {"element":"수", "element_state":"lack"}  # 부족/과다
    """
    # 지금은 기본값. (다음에 ohengAnalyzer 결과 연결)
    return {"element": "수", "element_state": "lack"}


# -----------------------------
# 2) 십신 연결(임시 기본값)
# -----------------------------
# TODO: 십신 엔진 붙이면 아래 함수만 교체하면 됩니다.
def infer_ten_god_context(pillars: Dict[str, Tuple[str, str]], domain: str) -> str:
    """
    domain에 따라 상담에서 가장 체감되는 십신을 임시로 고릅니다.
    나중에 sipsin 분석 결과로 자동 치환.
    """
    if domain == "money":
        return "정재"
    if domain == "people":
        return "관성"
    if domain == "health":
        return "인성"
    if domain == "event":
        return "비견"
    if domain == "mind":
        return "식상"
    return "정재"


# -----------------------------
# 3) 12운성 연결(신살 리스트에서 자동 추출)
# -----------------------------
def pick_main_lifestage(items: List[Dict[str, Any]]) -> str:
    """
    items 안에 12운성이 있으면 '가장 영향 큰 것'을 1개 고릅니다.
    기준: weight 우선, 없으면 day/hours 우선
    """
    stages = []
    for it in items:
        name = str(it.get("name", ""))
        if _is_lifestage(name):
            stages.append(it)

    if not stages:
        return "장생"  # 기본값(임시)

    def keyfn(x: Dict[str, Any]):
        w = int(x.get("weight", 1) or 1)
        where = str(x.get("where", ""))
        where_rank = {"day": 0, "hour": 1, "month": 2, "year": 3}.get(where, 9)
        return (-w, where_rank)

    stages.sort(key=keyfn)
    return _extract_lifestage(str(stages[0].get("name", "12운성:장생")))


# -----------------------------
# 4) 길흉 판정 + "어디로 오느냐" 분기
# -----------------------------
def classify_factor(it: Dict[str, Any]) -> str:
    """
    shinsal_score.py의 class가 있으면 그걸 우선 사용.
    없으면 이름 기반 대충 분류.
    """
    cls = str(it.get("class", "")).strip()
    if cls in ("good", "caution", "bad", "neutral"):
        return cls

    name = str(it.get("name", ""))
    if name in ("천을귀인",):
        return "good"
    if name in ("화개살", "도화"):
        return "caution"
    return "neutral"


def domain_of_factor(name: str) -> str:
    if _is_lifestage(name):
        return "flow"
    return DOMAIN_BY_SHINSAL.get(name, "event")


# -----------------------------
# 5) 최종 “상담가톤 + 감성 해결법” 문장 생성
# -----------------------------
def build_factor_consult(
    *,
    pillars: Dict[str, Tuple[str, str]],
    items: List[Dict[str, Any]],
    factor: Dict[str, Any],
) -> Dict[str, Any]:
    """
    factor 1개에 대해:
    - 원인(직관)
    - 조언(감성+실천)
    - 도메인(사람/돈/건강/사건/흐름)
    - 시기(기둥 where 기반 간단)
    반환
    """
    name = str(factor.get("name", ""))
    where = str(factor.get("where", "day"))
    w = int(factor.get("weight", 1) or 1)

    domain = domain_of_factor(name)
    element_ctx = infer_element_context(pillars)
    ten_god = infer_ten_god_context(pillars, domain)
    life_stage = pick_main_lifestage(items)

    # 시기 라벨(아주 간단 버전) - 다음에 대운/세운/월운으로 확장
    when = {
        "year": "올해 흐름",
        "month": "이번 달 흐름",
        "day": "오늘~이번 주 흐름",
        "hour": "지금 당장/단기 흐름",
    }.get(where, "가까운 시기")

    # 상담 문장 생성 (오슈님이 붙여넣은 엔진 호출)
    consult = build_consult_sentence(
        element=element_ctx["element"],
        element_state=element_ctx["element_state"],
        ten_god=ten_god,
        shinsal=name,
        life_stage=life_stage,
    )

    cls = classify_factor(factor)

    # “길할 때 제스처 / 흉할 때 대처”를 도메인별로 덧붙임
    gesture = _gesture_guide(domain=domain, cls=cls)

    return {
        "name": name,
        "class": cls,
        "where": where,
        "when": when,
        "weight": w,
        "domain": domain,
        "cause": consult.get("cause", ""),
        "advice": consult.get("advice", ""),
        "gesture": gesture,
    }


def _gesture_guide(*, domain: str, cls: str) -> str:
    """
    길할 때는 '밀어붙이는 제스처', 흉/주의는 '피하는 제스처'
    (상담가톤: 직관적으로 말하고, 방법은 감성적으로)
    """
    if cls == "good":
        if domain == "people":
            return "사람운이 길하게 붙는 때예요. 먼저 연락·소개·제안, ‘내가 먼저 손 내미는’ 제스처가 운을 키웁니다."
        if domain == "money":
            return "돈운이 열리는 흐름입니다. 작게라도 ‘수익 행동’을 바로 실행하세요(정리·견적·홍보·협상)."
        if domain == "health":
            return "회복운이 붙습니다. 루틴(수면/식사/가벼운 운동)을 ‘끊기지 않게’ 잡는 게 제일 강합니다."
        if domain == "mind":
            return "정신이 맑아지는 흐름. 혼자 집중하는 시간(정리/독서/기도/명상)을 확보하면 운이 더 커져요."
        return "기회가 들어오는 흐름입니다. 미루지 말고 ‘당일 처리’가 운을 더 끌어올립니다."

    if cls in ("caution", "bad"):
        if domain == "people":
            return "사람으로 변수가 생기기 쉬워요. 말·돈·약속은 ‘증거 남기기(메모/문자)’가 방패입니다."
        if domain == "money":
            return "금전 변수 주의. 큰 결제/투자/대여는 보류, 통장·지출 ‘잠금’이 최고의 대처예요."
        if domain == "health":
            return "몸이 먼저 신호를 보내는 흐름. 무리·과로·음주 줄이고, 통증/증상은 ‘빨리 확인’이 답입니다."
        if domain == "event":
            return "돌발 변수가 끼기 쉬운 때. 이동·일정은 여유를 두고, 서류/계약은 재확인이 필요합니다."
        return "마음이 예민해지기 쉬워요. 혼자 끌어안지 말고, 감정 배출(산책/호흡/기록)로 눌러주세요."

    # neutral
    return "무난한 흐름입니다. ‘정리-루틴-점검’만 해도 손해가 안 납니다."


# -----------------------------
# 6) 전체 요약 라인 (B단계)
# -----------------------------
def build_summary_lines(summary: Dict[str, Any]) -> List[str]:
    """
    B단계 요약 문장 (상담가톤 + 감성)
    """
    verdict_label = str(summary.get("verdict_label", "보통(혼재)"))
    counts = summary.get("counts", {})
    score = summary.get("score", {})

    good = int(counts.get("good", 0) or 0)
    caution = int(counts.get("caution", 0) or 0)
    bad = int(counts.get("bad", 0) or 0)
    total = int(counts.get("total", 0) or (good + caution + bad))

    total_score = int(score.get("total", 0) or 0)

    lines = []
    lines.append(f"- 총평: {verdict_label} (좋음 {good} / 주의 {caution} / 흉 {bad})")
    lines.append(f"- 흐름 포인트: 전체 점수 {total_score} 기준으로, ‘좋은 쪽은 바로 밀고’ ‘주의는 잠그는’ 전략이 유리합니다.")
    if bad >= 1:
        lines.append("- 핵심: 변수가 ‘생기기 전’에 차단하면 됩니다. 약속/돈/몸 컨디션을 먼저 잠그세요.")
    elif caution >= 1:
        lines.append("- 핵심: 큰 사고는 아니고, 말·돈·컨디션에서 작은 삐끗이 나기 쉬운 흐름입니다.")
    else:
        lines.append("- 핵심: 무난합니다. 정리와 루틴만 지켜도 운이 떨어지지 않습니다.")
    return lines
