# -*- coding: utf-8 -*-
"""
solar_terms_compute.py  (실시간 계산기)
- pyephem으로 태양의 황경을 계산해 24절기/중기 시각을 산출합니다.
- 제공 함수:
    * compute_all_terms(year): 24절기 전체(0,15,...,345)
    * compute_principal_terms(year): 중기 12개(0/30/.../330)
- 반환 형태:
    [{"degree": int, "time_utc": "YYYY-MM-DDTHH:MM:SS+00:00"}, ...]
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, cast

import ephem  # type: ignore[reportMissingImports]

# Pylance: ephem 동적 모듈
_ephem = cast(Any, ephem)


ALL_DEGS: List[int] = [i * 15 for i in range(24)]  # 0,15,30,...,345
PRINCIPAL_DEGS: List[int] = [d for d in ALL_DEGS if d % 30 == 0]  # 0,30,60,...,330


def _dt_utc_naive_for_ephem(dt_utc: datetime) -> datetime:
    """PyEphem ephem.Date()는 UTC naive datetime을 기대하는 경우가 많음."""
    assert dt_utc.tzinfo is not None, "dt_utc must be timezone-aware (UTC)"
    return dt_utc.astimezone(timezone.utc).replace(tzinfo=None)


def _sun_ecl_lon_deg(dt_utc: datetime) -> float:
    """해당 UTC 시각의 태양 황경(도, 0~360)."""
    naive = _dt_utc_naive_for_ephem(dt_utc)
    sun = _ephem.Sun(_ephem.Date(naive))
    ecl = _ephem.Ecliptic(sun)
    lon = float(ecl.lon) * 180.0 / math.pi  # rad → deg
    if lon < 0:
        lon += 360.0
    return lon


def _ang_diff(a: float, b: float) -> float:
    """(a - b)을 [-180, +180] 범위로 정규화."""
    return (a - b + 180.0) % 360.0 - 180.0


def _bisect(target_deg: float, t0: datetime, t1: datetime,
            tol_seconds: int = 1, max_iter: int = 100) -> datetime:
    """
    [t0, t1] 구간에서 태양 황경 == target_deg가 되는 시각을 이분 탐색으로 근사.
    t0/t1은 tz=UTC 필요. 스캔 단계에서 f(t0)·f(t1) <= 0 인 구간만 넘길 것.
    """
    f0 = _ang_diff(_sun_ecl_lon_deg(t0), target_deg)
    f1 = _ang_diff(_sun_ecl_lon_deg(t1), target_deg)

    if f0 == 0:
        return t0
    if f1 == 0:
        return t1
    if f0 * f1 > 0:
        raise ValueError("bisect bracket: endpoints same sign (no root guaranteed)")

    left, right = t0, t1
    fl, fr = f0, f1

    for _ in range(max_iter):
        if (right - left).total_seconds() <= tol_seconds:
            return left
        mid = left + (right - left) / 2
        fm = _ang_diff(_sun_ecl_lon_deg(mid), target_deg)
        if abs(fm) < 1e-9:
            return mid
        # 근이 [left, mid]에 있으면 fl·fm <= 0
        if fl * fm <= 0:
            right, fr = mid, fm
        else:
            left, fl = mid, fm

    return left


def _scan_degrees(year: int, degrees: List[int]) -> List[Dict[str, Any]]:
    """
    주어진 각도 집합에 대해 해당 연도의 절입 시각들을 계산.
    - 6시간 스캔 → 미검출 시 1시간 스캔 → 이분탐색으로 1초 이내로 보정
    """
    t_start = datetime(year, 1, 1, 0, 0, tzinfo=timezone.utc)
    t_end = datetime(year + 1, 1, 1, 6, 0, tzinfo=timezone.utc)  # 여유 6시간
    step1 = timedelta(hours=6)
    step2 = timedelta(hours=1)

    results: List[Dict[str, Any]] = []
    for deg in degrees:
        t = t_start
        prev = _ang_diff(_sun_ecl_lon_deg(t), deg)
        found: tuple[datetime, datetime] | None = None
        while t <= t_end:
            t_next = t + step1
            cur = _ang_diff(_sun_ecl_lon_deg(t_next), deg)
            if prev * cur <= 0:
                found = (t, t_next)
                break
            t = t_next
            prev = cur

        if not found:
            t = t_start
            prev = _ang_diff(_sun_ecl_lon_deg(t), deg)
            while t <= t_end:
                t_next = t + step2
                cur = _ang_diff(_sun_ecl_lon_deg(t_next), deg)
                if prev * cur <= 0:
                    found = (t, t_next)
                    break
                t = t_next
                prev = cur

        if found:
            hit = _bisect(deg, found[0], found[1], tol_seconds=1, max_iter=100)
            results.append({
                "degree": int(deg),
                "time_utc": hit.isoformat().replace("+00:00", "") + "+00:00",
            })

    results.sort(key=lambda x: x["time_utc"])
    return results


def compute_all_terms(year: int) -> List[Dict[str, Any]]:
    """해당 연도의 24절기 전체(0,15,...,345)."""
    return _scan_degrees(year, ALL_DEGS)


def compute_principal_terms(year: int) -> List[Dict[str, Any]]:
    """해당 연도의 중기 12개(0/30/.../330)."""
    return _scan_degrees(year, PRINCIPAL_DEGS)
