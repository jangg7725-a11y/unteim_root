# -*- coding: utf-8 -*-
"""
engine.daewoonCalculator
- 대운 계산 (절입일 보정 + 월주 기준)
- 월지 결정: 절기 경계(평균 절기 폴백) 우선, 실패 시 양력월 근사 폴백
"""

from __future__ import annotations
from typing import List, Dict, Literal, Tuple
from datetime import datetime

from .kasi_client import (
    get_next_solar_term_after,
    get_solar_terms_for_year,
    SOLAR_TERM_TO_BRANCH,
    MONTH_BOUNDARY_TERMS,
    KST,
)

HEAVENLY_STEMS = ["갑","을","병","정","무","기","경","신","임","계"]
EARTHLY_BRANCHES = ["자","축","인","묘","진","사","오","미","신","유","술","해"]
BRANCH_INDEX = {b:i for i,b in enumerate(EARTHLY_BRANCHES)}

# 양력월 → 월지(근사) 폴백
MONTH_TO_BRANCH_FALLBACK = {
    1: BRANCH_INDEX["축"],  2: BRANCH_INDEX["인"],  3: BRANCH_INDEX["묘"],
    4: BRANCH_INDEX["진"],  5: BRANCH_INDEX["사"],  6: BRANCH_INDEX["오"],
    7: BRANCH_INDEX["미"],  8: BRANCH_INDEX["신"],  9: BRANCH_INDEX["유"],
    10: BRANCH_INDEX["술"], 11: BRANCH_INDEX["해"], 12: BRANCH_INDEX["자"],
}

Gender = Literal["남","여"]
YinYang = Literal["양","음"]

def year_ganji(year: int) -> str:
    stem = HEAVENLY_STEMS[(year - 1984) % 10]
    branch = EARTHLY_BRANCHES[(year - 1984) % 12]
    return stem + branch

def year_stem_index(year: int) -> int:
    return (year - 1984) % 10

def _direction_by_gender_yinyang(gender: Gender, yin_yang: YinYang) -> int:
    return +1 if (gender=="남" and yin_yang=="양") or (gender=="여" and yin_yang=="음") else -1

def compute_start_age_from_solar_term(birth_dt_kst: datetime) -> Tuple[int,int,float]:
    next_term_dt = get_next_solar_term_after(birth_dt_kst).timestamp_kst
    diff = next_term_dt - birth_dt_kst
    total_days = diff.total_seconds()/86400.0
    yf = total_days/3.0
    y = int(yf); m = int((yf-y)*12.0 + 1e-9)
    return y, m, yf

# === 절기 경계 기반 월지 계산 ===
def month_branch_index_by_solar_terms_precise(dt_kst: datetime) -> Tuple[int,str]:
    """
    절기표(해당 연도 및 필요 시 이전/다음 연도)로 월지(지지 인덱스)를 정확히 계산.
    구간:
      [입춘~경칩)=寅, [경칩~청명)=卯, ... , [대설~소한)=子, [소한~다음해 입춘)=丑
    """
    try:
        y = dt_kst.year
        tbl_this = get_solar_terms_for_year(y)
        tbl_prev = get_solar_terms_for_year(y-1)
        tbl_next = get_solar_terms_for_year(y+1)

        # 경계 리스트 만들기: (경계시각, 경계이름)
        # … , (prev_소한), (this_입춘), (this_경칩), … , (this_대설), (this_소한), (next_입춘) …
        boundaries: List[Tuple[datetime, str]] = []
        if "소한" in tbl_prev:
            boundaries.append((tbl_prev["소한"], "소한(prev)"))
        if "입춘" in tbl_this:
            boundaries.append((tbl_this["입춘"], "입춘"))
        for name in MONTH_BOUNDARY_TERMS[1:11]:  # 경칩~대설
            if name in tbl_this:
                boundaries.append((tbl_this[name], name))
        if "소한" in tbl_this:
            boundaries.append((tbl_this["소한"], "소한"))
        if "입춘" in tbl_next:
            boundaries.append((tbl_next["입춘"], "입춘(next)"))

        boundaries.sort(key=lambda x: x[0])

        # dt_kst가 속한 구간의 '시작 경계'를 찾는다
        last_name = None
        for t, name in boundaries:
            if t <= dt_kst:
                last_name = name
            else:
                break

        # 경계 이름 → 월지
        # suffix 제거: "소한(prev)" → "소한"
        if last_name:
            key = last_name.split("(")[0]
            if key in SOLAR_TERM_TO_BRANCH:
                bchar = SOLAR_TERM_TO_BRANCH[key]
                return BRANCH_INDEX[bchar], "solar_terms"
    except Exception:
        pass
    # 실패 시 폴백
    return MONTH_TO_BRANCH_FALLBACK[dt_kst.month], "gregorian_fallback"

def month_stem_index_from_year_stem(year_stem_idx: int, month_branch_idx: int) -> int:
    IN = BRANCH_INDEX["인"]
    if year_stem_idx in (0,5):   start_for_in = 2  # 丙
    elif year_stem_idx in (1,6): start_for_in = 4  # 戊
    elif year_stem_idx in (2,7): start_for_in = 6  # 庚
    elif year_stem_idx in (3,8): start_for_in = 8  # 壬
    else:                        start_for_in = 0  # 甲
    offset = (month_branch_idx - IN) % 12
    return (start_for_in + offset) % 10

def calculate_daewoon(
    birth_year: int,
    gender: Gender,
    yin_yang: YinYang,
    birth_month: int | None = None,
    birth_day: int | None = None,
    birth_hour: int | None = None,
    birth_minute: int | None = None,
    num_cycles: int = 8,
    override_start_age: int | None = None,
    use_month_pillar: bool = True,
) -> List[Dict[str, object]]:

    direction = _direction_by_gender_yinyang(gender, yin_yang)

    # 시작세
    if override_start_age is not None:
        start_age = override_start_age
        start_age_detail = {"mode":"override","years":start_age,"months":0}
        birth_dt_for_month = None
    elif (birth_month is not None and birth_day is not None and
          birth_hour is not None and birth_minute is not None):
        bm,bd,bh,bmin = int(birth_month),int(birth_day),int(birth_hour),int(birth_minute)
        birth_dt = datetime(birth_year,bm,bd,bh,bmin,tzinfo=KST)
        y,m,yf = compute_start_age_from_solar_term(birth_dt)
        start_age = max(1,y)
        start_age_detail = {"mode":"solar_term","years":y,"months":m,"years_float":round(yf,3)}
        birth_dt_for_month = birth_dt
    else:
        start_age = 10
        start_age_detail = {"mode":"default","years":start_age,"months":0}
        birth_dt_for_month = None

    # 시작 간지(월주 or 연주)
    if use_month_pillar and (birth_month is not None):
        if birth_dt_for_month is None:
            birth_dt_for_month = datetime(birth_year, int(birth_month), 15, 12, 0, tzinfo=KST)

        m_branch_idx, month_mode = month_branch_index_by_solar_terms_precise(birth_dt_for_month)
        y_stem_idx = year_stem_index(birth_year)
        m_stem_idx = month_stem_index_from_year_stem(y_stem_idx, m_branch_idx)
        base_stem_idx = m_stem_idx
        base_branch_idx = m_branch_idx
        base_mode = f"month_pillar({month_mode})"
    else:
        base_stem_idx = year_stem_index(birth_year)
        base_branch_idx = (birth_year - 1984) % 12
        base_mode = "year_pillar"

    # 대운 리스트
    results: List[Dict[str, object]] = []
    for i in range(num_cycles):
        si = (base_stem_idx + direction * i) % 10
        ji = (base_branch_idx + direction * i) % 12
        results.append({"age": start_age + i*10, "ganji": HEAVENLY_STEMS[si] + EARTHLY_BRANCHES[ji]})

    results.append({
        "__meta__": {
            "start_age_detail": start_age_detail,
            "direction": "순행" if direction==1 else "역행",
            "base_mode": base_mode,
            "base_pillar_ganji": HEAVENLY_STEMS[base_stem_idx] + EARTHLY_BRANCHES[base_branch_idx],
            "birth_year_ganji": year_ganji(birth_year),
            "month_mode": month_mode if use_month_pillar else "n/a",
        }
    })
    return results

if __name__ == "__main__":
    sample = calculate_daewoon(
        birth_year=1966, gender="여", yin_yang="양",
        birth_month=11, birth_day=4, birth_hour=2, birth_minute=5,
        num_cycles=8, use_month_pillar=True,
    )
    print("대운 계산 예시(절기 경계 기반 월지):", sample)
