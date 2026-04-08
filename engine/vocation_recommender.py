# -*- coding: utf-8 -*-
"""
vocation_recommender.py
사주 기반 적성/천직 추천 (룰베이스 v1)
- 입력: 일간, 오행 분포, 십신 분포, 용희(추정), 12운성(월지 기준)
- 출력: 추천 직종 리스트(점수/근거), 상위 카테고리 태그
"""

from typing import Dict, List, Tuple

# 간단 가중치 테이블 (필요시 조정)
W = {
    "useful_god": 3,      # 용/희신과 직업 키워드 일치
    "five_el_balance": 2, # 오행 분포가 직업 성격과 합치
    "ten_gods": 2,        # 십신 성격과 직업 성격 합치
    "twelve_stage": 1,    # 12운성 단계 보정 (생산성/표현성/사회성)
}

# 직업 카테고리 ↔ 성향 매핑 (요약형)
#   - 오행: 木 창의/교육/기획, 火 표현/미디어/의료, 土 운영/부동산/인사, 金 법/공무/금융/제조, 水 IT/물류/리서치/무역
#   - 십신: 재성(영업/재무), 관성(공무/법/관리), 인성(연구/교육), 식상(콘텐츠/개발/디자인/자영), 비겁(창업/리더/조직운영)
CATEGORIES: Dict[str, Dict] = {
    "교육·연구(목/인성)":   {"el": ["목"], "tg": ["정인","편인"], "keywords": ["교육","연구","학습","코칭","상담"], "examples": ["교사","강사","멘토","연구원","심리상담"]},
    "콘텐츠·디자인·개발(화/식상)": {"el": ["화"], "tg": ["식신","상관"], "keywords": ["표현","크리에이티브","개발","디자인"], "examples": ["콘텐츠PD","유튜버","디자이너","프론트엔드","카피라이터"]},
    "운영·부동산·HR(토/비겁)": {"el": ["토"], "tg": ["비견","겁재"], "keywords": ["조직","운영","조율","부동산"], "examples": ["운영매니저","PM/PO","HR","부동산중개","PMO"]},
    "법·공무·제조·금융(金/관성)": {"el": ["금"], "tg": ["정관","편관"], "keywords": ["규범","품질","통제","리스크"], "examples": ["공무원","법무/컴플","품질관리","리스크관리","자산운용"]},
    "IT·데이터·무역·물류(수/재성)": {"el": ["수"], "tg": ["정재","편재"], "keywords": ["분석","디지털","유통","자금흐름"], "examples": ["데이터분석","백엔드","무역실무","물류","세일즈파이낸스"]},
    "창업·영업리더(비겁/재성/식상)": {"el": ["목","화","토","수"], "tg": ["비견","겁재","정재","편재","식신","상관"], "keywords": ["개척","매출","확장"], "examples": ["창업자","BM개발","영업총괄","프리랜서"]},
    "의료·헬스케어(화/인성·식상)": {"el": ["화"], "tg": ["정인","편인","식신"], "keywords": ["치료","케어","건강"], "examples": ["간호/치료사","의료코디","피트니스코치","영양"]},
}

# 12운성 보정: 생산/표현/관리 적성 강화 구간
STAGE_HINT = {
    "제왕": {"boost": ["창업·영업리더(비겁/재성/식상)","콘텐츠·디자인·개발(화/식상)"]},
    "건록": {"boost": ["법·공무·제조·금융(金/관성)","운영·부동산·HR(토/비겁)"]},
    "관대": {"boost": ["교육·연구(목/인성)","IT·데이터·무역·물류(수/재성)"]},
    "병":   {"boost": []},  # 감점 없이 유지
    "쇠":   {"boost": []},
}

def _score_el(five: Dict[str, int], els: List[str]) -> int:
    # els에 해당하는 오행이 +면 가점, 심한 음수면 감점
    s = 0
    for e in els:
        v = five.get(e, 0)
        if v >= 2:   s += 2
        elif v == 1: s += 1
        elif v <= -2: s -= 2
        elif v == -1: s -= 1
    return s

def _score_tg(ten: Dict[str, int], tg_list: List[str]) -> int:
    s = 0
    for t in tg_list:
        v = ten.get(t, 0)
        if v >= 2:   s += 2
        elif v == 1: s += 1
        elif v <= -2: s -= 2
        elif v == -1: s -= 1
    return s

def _score_useful(useful: List[str], cat_name: str) -> int:
    # 용희신(예: 목·화가 용/희)과 카테고리 오행 키워드 매칭 시 가점
    el_keys = CATEGORIES[cat_name]["el"]
    return 1 if any(u in el_keys for u in useful) else 0

def _stage_boost(stage: str, cat_name: str) -> int:
    boosts = STAGE_HINT.get(stage, {}).get("boost", [])
    return 1 if cat_name in boosts else 0

def recommend_vocations(
    day_master: str,
    five_elements: Dict[str, int],      # {"목":2,"화":1,"토":0,"금":-1,"수":1}
    ten_gods: Dict[str, int],           # {"정재":1,"편재":2,"정관":-1,...}
    useful_elements: List[str],         # 용·희신 후보 ["목","화"]
    stage_12: str                       # 월지 기준 12운성(예: "제왕","건록","관대"...)
) -> List[Tuple[str,int,List[str]]]:
    """
    반환: [(카테고리, 점수, 근거리스트)] 점수 내림차순
    """
    results: List[Tuple[str,int,List[str]]] = []
    for cat, spec in CATEGORIES.items():
        s = 0
        reasons: List[str] = []
        # 오행 적합도
        es = _score_el(five_elements, spec["el"]) * W["five_el_balance"]
        if es: reasons.append(f"오행적합 {es:+d}")
        s += es
        # 십신 적합도
        ts = _score_tg(ten_gods, spec["tg"]) * W["ten_gods"]
        if ts: reasons.append(f"십신적합 {ts:+d}")
        s += ts
        # 용희신 보정
        us = _score_useful(useful_elements, cat) * W["useful_god"]
        if us: reasons.append(f"용희신보정 {us:+d}")
        s += us
        # 12운성 보정
        bs = _stage_boost(stage_12, cat) * W["twelve_stage"]
        if bs: reasons.append(f"12운성 {stage_12} {bs:+d}")
        s += bs

        # 점수와 근거 정리
        results.append((cat, s, reasons))

    # 점수 내림차순, 동점이면 이름순
    results.sort(key=lambda x: (-x[1], x[0]))
    return results
