# unteim/engine/astro_solar_terms.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import List, Optional, Tuple, Dict, Any
from functools import lru_cache

import numpy as np
from skyfield.api import load
from skyfield.framelib import ecliptic_frame
from skyfield import almanac

KST = ZoneInfo("Asia/Seoul")
_TS = load.timescale()
_EPH = load("de421.bsp")

# 태양 황경 λ에 대해 floor(λ/15)=k (0~23)일 때 해당 15° 구간의 절기명.
# (k=0 → 춘분/0°, k=1 → 청명/15°, … k=21 → 입춘/315°, k=22 → 우수, k=23 → 경칩)
# 기존 SOLAR_TERM_NAMES(입춘부터 나열)와 skyfield 버킷 인덱스가 어긋나 월지가 틀어지던 문제를 방지.
LONGITUDE_BUCKET_TO_TERM_NAME = [
    "춘분", "청명", "곡우", "입하", "소만", "망종",
    "하지", "소서", "대서", "입추", "처서", "백로",
    "추분", "한로", "상강", "입동", "소설", "대설",
    "동지", "소한", "대한", "입춘", "우수", "경칩",
]

# 호환: 기존 import 이름 유지 (내용은 황경 버킷 순)
SOLAR_TERM_NAMES = LONGITUDE_BUCKET_TO_TERM_NAME


@dataclass(frozen=True)
class SolarTerm:
    name: str
    degree: float
    dt_kst: datetime


def _to_kst(t) -> datetime:
    """Skyfield Time -> aware datetime(KST)"""
    dt_utc = t.utc_datetime()
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    return dt_utc.astimezone(KST)


def _solar_term_index_factory(eph):
    """
    태양 황경(longitude)을 0~23 구간으로 바꿔주는 함수(15도 단위).
    almanac.find_discrete()에 넣기 위해 내부함수로 생성.
    """
    sun = eph["sun"]
    earth = eph["earth"]

    def term_index(t):
        # 황경(도)
        lon = earth.at(t).observe(sun).apparent().frame_latlon(ecliptic_frame)[1].degrees
        lon = np.mod(lon, 360.0)
        idx = np.floor(lon / 15.0).astype(int)  # 0~23
        return idx

    return term_index


@lru_cache(maxsize=16)
def _compute_solar_terms_for_year_cached(year: int) -> Tuple[SolarTerm, ...]:
    """
    year에 해당하는 24절기 시각을 KST로 계산하여 반환.
    결과 길이는 항상 24를 목표로 합니다.
    """
    t0 = _TS.utc(year, 1, 1)
    t1 = _TS.utc(year + 1, 1, 1)

    f = _solar_term_index_factory(_EPH)
    f.step_days = 1
    times, values = almanac.find_discrete(t0, t1, f)

    # values는 0~23 절기 구간 인덱스
    # 같은 인덱스가 여러 번 잡힐 수 있어, "처음 등장"만 채택
    first_time_by_idx: Dict[int, Any] = {}
    for t, v in zip(times, values):
        idx = int(v)
        if idx not in first_time_by_idx:
            first_time_by_idx[idx] = t

    # 혹시 24개가 안 채워졌으면(매우 드묾) 안전 장치로 예외
    if len(first_time_by_idx) != 24:
        # 디버그 정보 포함
        got = sorted(first_time_by_idx.keys())
        raise RuntimeError(f"solar terms not complete: got {len(first_time_by_idx)} / 24, idx={got}")

    out: List[SolarTerm] = []
    for k in range(24):
        name = LONGITUDE_BUCKET_TO_TERM_NAME[k]
        degree = float(k) * 15.0
        t = first_time_by_idx[k]
        out.append(SolarTerm(name=name, degree=degree, dt_kst=_to_kst(t)))

    return tuple(out)


def compute_solar_terms_for_year(year: int) -> List[SolarTerm]:
    # 호출자는 list를 기대하므로 복사본을 반환한다.
    return list(_compute_solar_terms_for_year_cached(year))


def nearest_terms_around(dt_kst: datetime, terms: List[SolarTerm]) -> Tuple[Optional[SolarTerm], Optional[SolarTerm]]:
    """
    dt_kst 기준: 이전 절기(prev), 다음 절기(next) 반환
    """
    prev = None
    nxt = None
    for t in terms:
        if t.dt_kst <= dt_kst:
            if (prev is None) or (t.dt_kst > prev.dt_kst):
                prev = t
        if t.dt_kst > dt_kst:
            if (nxt is None) or (t.dt_kst < nxt.dt_kst):
                nxt = t
    return prev, nxt


def month_branch_index_by_terms(dt_kst: datetime, terms: List[SolarTerm]) -> int:
    """
    월지 전환을 '절기(입절)' 기준으로 잡을 때 쓰는 보조 함수.
    여기서는 단순히 "현재 dt가 몇 번째 절기 구간인지(0~23)"를 반환.
    (월운 엔진에서 원하는 방식으로 추가 매핑하면 됩니다)
    """
    prev, _ = nearest_terms_around(dt_kst, terms)
    if prev is None:
        return 0
    # degree 0~345 => index 0~23
    return int(round(prev.degree / 15.0)) % 24
