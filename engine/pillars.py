# -*- coding: utf-8 -*-
# pyright: reportAttributeAccessIssue=false
"""
사주 4주(년·월·일·시) 계산
- 연주 절입(立春) 기준 보정
- 월주는 24절기 중 '절(節, 315°, 345°, 15° ...)' 경계로 계산
- 일주는 JDN 기반 60갑자 산출 (기준일: 1984-02-02 00:00 KST = 甲子)
- 시주는 일간+시지 규칙으로 산출
주의: 일주 기준일은 관용 기준(1984-02-02 甲子)에 맞췄습니다.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Dict, Tuple, List

import pytz
from .solar_terms import find_term_times, get_principal_terms
from .lunar_kr import KST  # 동일 타임존 사용

# 간지 테이블
STEMS = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]

# (연간 기준) 寅월의 천간 시작표 (寅월의 천간)
# 甲/己 → 丙寅, 乙/庚 → 戊寅, 丙/辛 → 庚寅, 丁/壬 → 壬寅, 戊/癸 → 甲寅
Y_STEM_TO_YIN_GAN = {
    0: 2, 5: 2,   # 甲/己 -> 丙(2)
    1: 4, 6: 4,   # 乙/庚 -> 戊(4)
    2: 6, 7: 6,   # 丙/辛 -> 庚(6)
    3: 8, 8: 8,   # 丁/壬 -> 壬(8)
    4: 0, 9: 0    # 戊/癸 -> 甲(0)
}

# 시주: 일간에 따른 子시의 천간 시작표
# 甲/己: 甲子, 乙/庚: 丙子, 丙/辛: 戊子, 丁/壬: 庚子, 戊/癸: 壬子
D_STEM_TO_ZI_GAN = {
    0:0, 5:0,
    1:2, 6:2,
    2:4, 7:4,
    3:6, 8:6,
    4:8, 9:8
}

@dataclass
class Pillar:
    stem: str
    branch: str

def ganzhi_from_index(idx: int) -> Tuple[str, str]:
    return STEMS[idx % 10], BRANCHES[idx % 12]

def y_ganzhi_from_year_solar(dt_kst: datetime) -> Pillar:
    """
    연주: 절입(立春, 315°) 이전이면 전년도 간지.
    간지는 1984년(갑자) 기준으로 산출.
    """
    y = dt_kst.year
    # 해당 연도의 24절기에서 315°(입춘) 시각 찾기
    all_terms = find_term_times(y)
    lichun_kst = None
    for t in all_terms:
        if int(t["degree"]) == 315:  # 315° = 立春
            lichun_kst = datetime.fromisoformat(t["time_utc"]).astimezone(KST)
            break
    if lichun_kst is None:
        # 경계시 전후 연도에서 보강
        for yy in (y-1, y+1):
            for t in find_term_times(yy):
                if int(t["degree"]) == 315:
                    lichun_kst = datetime.fromisoformat(t["time_utc"]).astimezone(KST)
                    break
            if lichun_kst: break

    if lichun_kst is not None and dt_kst >= lichun_kst:
        year_for_gz = y
    else:
        year_for_gz = y - 1

    # 1984년이 甲子(갑자) 해
    base = 1984
    idx = (year_for_gz - base) % 60
    s, b = ganzhi_from_index(idx)
    return Pillar(s, b)

def m_ganzhi_from_solar(dt_kst: datetime, y_stem_idx: int) -> Pillar:
    """
    월주: 24절기 중 '절(節)' 경계(입춘, 경칩, 청명, …)로 월지 결정.
    절 경계 각도: 315, 345, 15, 45, …, 285 (12개, 30° 간격으로 315에서 시작)
    寅월부터 시작.
    월간은 '연간 → 寅월 시작천간' 표로 결정 후 월마다 +1.
    """
    y = dt_kst.year
    terms = find_term_times(y)
    # 절 각도 순서
    JIE_DEGS = [(315 + 30*i) % 360 for i in range(12)]
    # 해당 절의 KST 시각 테이블
    jie_times: List[datetime] = []
    for deg in JIE_DEGS:
        for t in terms:
            if int(t["degree"]) == deg:
                jie_times.append(datetime.fromisoformat(t["time_utc"]).astimezone(KST))
                break
        else:
            # 인접 연도에서 보강
            for yy in (y-1, y+1):
                for t in find_term_times(yy):
                    if int(t["degree"]) == deg:
                        jie_times.append(datetime.fromisoformat(t["time_utc"]).astimezone(KST))
                        break
                if len(jie_times) > 0 and jie_times[-1].tzinfo is not None:
                    break
    # 월지 index 찾기 (寅=2부터 시작, 子=0)
    month_index = None
    for i in range(len(jie_times)):
        start = jie_times[i]
        end = jie_times[(i+1) % len(jie_times)]
        if i == len(jie_times)-1:
            # 마지막 절 ~ 다음 해 첫 절
            if dt_kst >= start or dt_kst < end:
                month_index = (2 + i) % 12  # 寅을 2로 설정
                break
        else:
            if start <= dt_kst < end:
                month_index = (2 + i) % 12
                break
    if month_index is None:
        month_index = 2  # 폴백: 寅

    # 월간: 연간 기반 표에서 寅월 시작 간 얻고, (월차)만큼 +1
    yin_gan_idx = Y_STEM_TO_YIN_GAN[y_stem_idx]
    # 寅(2)부터 month_index까지의 차이
    steps = (month_index - 2) % 12
    m_gan_idx = (yin_gan_idx + steps) % 10

    return Pillar(STEMS[m_gan_idx], BRANCHES[month_index])

def jdn_from_datetime_kst(dt_kst: datetime) -> int:
    """유닉스 대신 JDN 사용 (날짜만 정확히, KST 기준으로 계산)"""
    y = dt_kst.year
    m = dt_kst.month
    d = dt_kst.day
    a = (14 - m)//2
    y2 = y + 4800 - a
    m2 = m + 12*a - 3
    jdn = d + (153*m2 + 2)//5 + 365*y2 + y2//4 - y2//100 + y2//400 - 32045
    return jdn

def d_ganzhi_from_solar(dt_kst: datetime) -> Pillar:
    """
    일주: JDN 기준으로 60갑자 산출
    기준일: 1984-02-02 00:00 KST = 甲子 (관용 기준)
    """
    base = KST.localize(datetime(1984, 2, 2, 0, 0))
    jdn_base = jdn_from_datetime_kst(base)
    jdn_cur = jdn_from_datetime_kst(dt_kst)
    idx = (jdn_cur - jdn_base) % 60  # 0 → 甲子
    s, b = ganzhi_from_index(idx)
    return Pillar(s, b)

def h_ganzhi_from_solar(dt_kst: datetime, d_stem_idx: int) -> Pillar:
    """
    시주: 2시간 단위. 子=23:00~00:59
    """
    hour = dt_kst.hour
    # 시지 index
    # 23:00~00:59 → 子(0), 01:00~02:59 → 丑(1), ...
    branch_idx = ((hour + 1) // 2) % 12
    # 子시의 간은 일간에 따라 달라짐
    zi_gan_idx = D_STEM_TO_ZI_GAN[d_stem_idx]
    h_gan_idx = (zi_gan_idx + branch_idx) % 10
    return Pillar(STEMS[h_gan_idx], BRANCHES[branch_idx])

def calc_four_pillars(dt_kst: datetime) -> Dict[str, Dict[str, str]]:
    """KST datetime → 4주 반환"""
    if dt_kst.tzinfo is None:
        dt_kst = KST.localize(dt_kst)

    # 연주
    y_p = y_ganzhi_from_year_solar(dt_kst)
    y_stem_idx = STEMS.index(y_p.stem)

    # 월주 (절기 경계 반영)
    m_p = m_ganzhi_from_solar(dt_kst, y_stem_idx)

    # 일주
    d_p = d_ganzhi_from_solar(dt_kst)
    d_stem_idx = STEMS.index(d_p.stem)

    # 시주
    h_p = h_ganzhi_from_solar(dt_kst, d_stem_idx)

    return {
        "year": {"stem": y_p.stem, "branch": y_p.branch},
        "month": {"stem": m_p.stem, "branch": m_p.branch},
        "day": {"stem": d_p.stem, "branch": d_p.branch},
        "hour": {"stem": h_p.stem, "branch": h_p.branch},
    }
