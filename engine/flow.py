# -*- coding: utf-8 -*-

from __future__ import annotations
from typing import Dict, List, Tuple
from datetime import datetime
from zoneinfo import ZoneInfo

from .pillars import STEMS, BRANCHES, y_ganzhi_from_year_solar
from .oheng import STEM_OHENG, BRANCH_OHENG

KST = ZoneInfo("Asia/Seoul")

def _sb_to_idx(stem: str, branch: str) -> int:
    for i in range(60):
        if STEMS[i % 10] == stem and BRANCHES[i % 12] == branch:
            return i
    return 0

def _idx_step(idx: int, step: int) -> int:
    return (idx + step) % 60

def _round_score(score: Dict[str, float], ndigits: int = 2) -> Dict[str, float]:
    return {k: round(v, ndigits) for k, v in score.items()}

def build_yearly_flow(
    birth_kst: datetime,
    sex: str,
    pillars: Dict[str, Dict[str, str]],
    dayun: Dict[str, object],
    span_years: int = 60,
    start_from_dayun_start: bool = True,
) -> List[Dict[str, object]]:
    """
    연도별 합성 흐름 (대운 + 세운)
    element_score = (대운간*2.0 + 대운지*1.4 + 세운간*1.0 + 세운지*0.7)
    반환 항목:
      - year
      - dayun_order, dayun_pillar
      - year_pillar (세운)
      - element_score (반올림)
      - combined (합성에 사용된 천간/지지)
    """
    if birth_kst.tzinfo is None:
        birth_kst = birth_kst.replace(tzinfo=KST)

    start_dt = datetime.strptime(str(dayun["start_datetime_kst"]), "%Y-%m-%d %H:%M")
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=KST)

    forward = (dayun["direction"] == "forward")
    step = 1 if forward else -1

    m_idx = _sb_to_idx(pillars["month"]["stem"], pillars["month"]["branch"])

    flows: List[Dict[str, object]] = []
    anchor_year = start_dt.year if start_from_dayun_start else birth_kst.year
    end_year = anchor_year + span_years

    for y in range(anchor_year, end_year):
        years_from_start = y - start_dt.year
        order = (years_from_start // 10) + 1 if years_from_start >= 0 else 0

        du_idx = m_idx if order <= 0 else _idx_step(m_idx, step * order)
        du_stem, du_branch = STEMS[du_idx % 10], BRANCHES[du_idx % 12]

        yp = y_ganzhi_from_year_solar(datetime(y, 6, 1, tzinfo=KST))
        yr_stem, yr_branch = yp.stem, yp.branch

        score = {"木": 0.0, "火": 0.0, "土": 0.0, "金": 0.0, "水": 0.0}
        def add(elem: str, w: float):
            if elem:
                score[elem] += w

        add(STEM_OHENG.get(du_stem, ""), 2.0)
        add(BRANCH_OHENG.get(du_branch, ""), 1.4)
        add(STEM_OHENG.get(yr_stem, ""), 1.0)
        add(BRANCH_OHENG.get(yr_branch, ""), 0.7)

        flows.append({
            "year": y,
            "dayun_order": order,
            "dayun_pillar": {"stem": du_stem, "branch": du_branch},
            "year_pillar": {"stem": yr_stem, "branch": yr_branch},
            "combined": {"stems": [du_stem, yr_stem], "branches": [du_branch, yr_branch]},
            "element_score": _round_score(score, 2),
        })

    return flows

def combine_one_year(
    year: int,
    birth_kst: datetime,
    pillars: Dict[str, Dict[str, str]],
    dayun: Dict[str, object]
) -> Dict[str, object]:
    """특정 연도 1건만 합성해서 반환 (도구 함수)"""
    flows = build_yearly_flow(birth_kst, "M", pillars, dayun, span_years=1)
    # 위 함수는 범위를 year부터 만들도록 설계되어 있지 않으니 간단히 찾아서 반환
    for row in flows:
        if row["year"] == year:
            return row
    return flows[0]
