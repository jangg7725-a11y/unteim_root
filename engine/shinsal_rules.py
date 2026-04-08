# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, Tuple, List

# ─────────────────────────────────────────────────────────────
# 표준 정의
STEMS = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
LIFESTAGE = ["장생","목욕","관대","임관","제왕","쇠","병","사","묘","절","태","양"]

# 한글 → 한자 표준화
STEM_KO2HZ: Dict[str, str] = {"갑":"甲","을":"乙","병":"丙","정":"丁","무":"戊","기":"己","경":"庚","신":"辛","임":"壬","계":"癸"}
BRANCH_KO2HZ: Dict[str, str] = {"자":"子","축":"丑","인":"寅","묘":"卯","진":"辰","사":"巳","오":"午","미":"未","신":"申","유":"酉","술":"戌","해":"亥"}

# 양/음 간
STEM_YANG = {"甲","丙","戊","庚","壬"}
STEM_YIN  = {"乙","丁","己","辛","癸"}

# 오행 by 천간
ELEMENT_BY_STEM = {
    "甲":"木","乙":"木",
    "丙":"火","丁":"火",
    "戊":"土","己":"土",
    "庚":"金","辛":"金",
    "壬":"水","癸":"水",
}
# 장생 시작지(오행 기준)
CHANGSHENG_START_BY_ELEMENT = {
    "木":"亥",
    "火":"寅",
    "土":"申",
    "金":"巳",
    "水":"申",
}

# ─────────────────────────────────────────────────────────────
# 유틸

def _norm_stem(s: str) -> str:
    s = s.strip()
    return STEM_KO2HZ.get(s, s)

def _norm_branch(b: str) -> str:
    b = b.strip()
    return BRANCH_KO2HZ.get(b, b)

def _ring_index(seq: List[str], x: str) -> int:
    try:
        return seq.index(x)
    except ValueError:
        raise ValueError(f"지원하지 않는 기호: {x}")

def twelve_lifestage(day_stem: str, target_branch: str) -> str:
    """일간/지지로 12운성 반환 (한글/한자 모두 허용)"""
    stem = _norm_stem(day_stem)
    br   = _norm_branch(target_branch)
    if stem not in ELEMENT_BY_STEM:
        raise ValueError(f"지원하지 않는 일간: {day_stem}")
    element = ELEMENT_BY_STEM[stem]
    start_br = CHANGSHENG_START_BY_ELEMENT[element]

    start_i = _ring_index(BRANCHES, start_br)
    tgt_i   = _ring_index(BRANCHES, br)
    step    = 1 if stem in STEM_YANG else -1

    diff = (tgt_i - start_i) % 12
    # step = -1이면 역방향
    k = diff if step == 1 else (-diff % 12)
    return LIFESTAGE[k]

# ─────────────────────────────────────────────────────────────
# 60갑자 전표 생성

def _build_60_table() -> Dict[str, str]:
    """'甲子'..'癸亥'까지 60갑자 → 12운성 매핑 dict 생성"""
    table: Dict[str, str] = {}
    for i in range(60):
        stem = STEMS[i % 10]
        branch = BRANCHES[i % 12]
        key = f"{stem}{branch}"
        table[key] = twelve_lifestage(stem, branch)
    return table

LIFESTAGE_TABLE_60: Dict[str, str] = _build_60_table()

# ─────────────────────────────────────────────────────────────
# 편의 API

def lifestage_of(ganji: str) -> str:
    """
    '병오' / '丙午' / ('병','오') / ('丙','午') 모두 허용
    """
    if isinstance(ganji, tuple) and len(ganji) == 2:
        gs, bs = ganji
        return twelve_lifestage(gs, bs)

    ganji = str(ganji).strip()
    # 한글 2글자 or 한자 2글자 케이스 분해
    if len(ganji) == 2:
        g, b = ganji[0], ganji[1]
        return twelve_lifestage(g, b)

    # 공백/구분자 포함 케이스 처리: "병 오", "丙-午" 등
    for sep in (" ", "-", "_", ",", "/"):
        if sep in ganji:
            g, b = ganji.split(sep, 1)
            return twelve_lifestage(g.strip(), b.strip())

    # 못 나눴으면 에러
    raise ValueError(f"간지 파싱 실패: {ganji}")

# ─────────────────────────────────────────────────────────────
# (선택) 역조회: 운성 → 해당 갑자 목록
def reverse_index() -> Dict[str, List[str]]:
    inv: Dict[str, List[str]] = {name: [] for name in LIFESTAGE}
    for gj, stage in LIFESTAGE_TABLE_60.items():
        inv[stage].append(gj)
    return inv
