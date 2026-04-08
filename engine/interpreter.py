# unteim/engine/interpreter.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Tuple

# 천간/지지 → 오행
STEM_TO_ELEM = {
    "갑": "목", "을": "목",
    "병": "화", "정": "화",
    "무": "토", "기": "토",
    "경": "금", "신": "금",
    "임": "수", "계": "수",
}
BRANCH_TO_ELEM = {
    "자": "수", "축": "토", "인": "목", "묘": "목", "진": "토", "사": "화",
    "오": "화", "미": "토", "신": "금", "유": "금", "술": "토", "해": "수"
}

# 상생/상극
GEN = {"목": "화", "화": "토", "토": "금", "금": "수", "수": "목"}      # 내가 생하는 것
CTRL = {"목": "토", "토": "수", "수": "화", "화": "금", "금": "목"}    # 내가 극하는 것

def _el_of_ganji(gj: str) -> Tuple[str, str]:
    """ganji='갑자' → ('목','수') (천간,지지 오행)"""
    if not gj or len(gj) < 2: return ("", "")
    stem, branch = gj[0], gj[1]
    return STEM_TO_ELEM.get(stem, ""), BRANCH_TO_ELEM.get(branch, "")

def _ten_god(day_elem: str, other_elem: str, other_is_stem: bool) -> str:
    """
    아주 간단한 십성 판정:
    - same element: 비견/겁재 (천간=비견, 지지=겁재)
    - other == GEN[day]: 식신/상관 (천간=식신, 지지=상관)
    - other == GEN[other]==day: 정인/편인 (천간=정인, 지지=편인)  ← day를 생하는 것
    - other == CTRL[day]: 재성(정재/편재)
    - CTRL[other] == day: 관성(정관/편관)
    """
    if not day_elem or not other_elem: return ""
    if other_elem == day_elem:
        return "비견" if other_is_stem else "겁재"
    if GEN.get(day_elem) == other_elem:
        return "식신" if other_is_stem else "상관"
    if GEN.get(other_elem) == day_elem:   # other → day
        return "정인" if other_is_stem else "편인"
    if CTRL.get(day_elem) == other_elem:
        return "정재" if other_is_stem else "편재"
    if CTRL.get(other_elem) == day_elem:  # other 가 day 를 극
        return "정관" if other_is_stem else "편관"
    return ""

def short_advice(ten_god: str) -> str:
    m = {
        "비견": "협업·동료운. 나눔과 균형이 핵심.",
        "겁재": "경쟁·지출 주의. 독단은 손해.",
        "식신": "생산성↑ 실행력 좋음. 먹을복/건강운.",
        "상관": "표현·홍보 좋음. 윗사람과 마찰 주의.",
        "정재": "현금흐름/실익. 지출 계획 세우기.",
        "편재": "기회·영업운. 분산·리스크 관리!",
        "정관": "규칙·책임. 문서·공무·승진운.",
        "편관": "압박·변수. 법/규정 체크, 안전주의.",
        "정인": "학습·자격·멘토운. 정리·정비 최적.",
        "편인": "아이디어·전환. 과몰입/고립 주의.",
        "": "컨디션 점검과 기본에 충실하면 OK.",
    }
    return m.get(ten_god, m[""])

def interpret_day(day_ganji: str, base_pillar_ganji: str) -> str:
    """
    day_ganji : 일운 간지(예: '갑자')
    base_pillar_ganji : 기준 간지(월주 권장. 예: '기해')
    → '상관(화) | 표현·홍보 좋음...' 형태의 짧은 해석 문자열
    """
    d_stem_el, d_branch_el = _el_of_ganji(day_ganji)
    # 기준은 월주 천간 우선(없으면 지지)
    b_stem_el, b_branch_el = _el_of_ganji(base_pillar_ganji)
    base_el = b_stem_el or b_branch_el
    # 우선 천간 관계로 십성, 없으면 지지로 보조
    tg = _ten_god(base_el, d_stem_el, other_is_stem=True) or \
         _ten_god(base_el, d_branch_el, other_is_stem=False)
    el_label = d_stem_el or d_branch_el
    return f"{tg}({el_label}) | {short_advice(tg)}"
