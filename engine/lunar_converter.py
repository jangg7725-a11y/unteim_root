# -*- coding: utf-8 -*-
# pyright: reportAttributeAccessIssue=false, reportReturnType=false, reportArgumentType=false
"""
자체엔진: 음력 변환 + 윤달 판정 (Pylance 친화형)
- ephem으로 합삭(신월) 계산
- 각 음력월에 중기(30° 절기) 포함 여부 검사 → 없으면 윤달
- 1/21 ~ 2/20 사이 첫 합삭을 포함하는 달 = 정월(1월)
"""

from __future__ import annotations
from datetime import datetime, timedelta, timezone
import math
from typing import Any, cast, List, Dict, Optional

import ephem
import pytz
from .solar_terms import get_principal_terms

Ephem = cast(Any, ephem)
KST = pytz.timezone("Asia/Seoul")
# -----------------------
# 내부 유틸
# -----------------------
def _ecl_lon_sun(dt_utc: datetime) -> float:
    sun = Ephem.Sun(dt_utc)
    ecl = Ephem.Ecliptic(sun)
    lon = float(ecl.lon) * 180.0 / math.pi
    if lon < 0:
        lon += 360.0
    return lon


def _ecl_lon_moon(dt_utc: datetime) -> float:
    moon = Ephem.Moon(dt_utc)
    ecl = Ephem.Ecliptic(moon)
    lon = float(ecl.lon) * 180.0 / math.pi
    if lon < 0:
        lon += 360.0
    return lon


def _elongation(dt_utc: datetime) -> float:
    """달-태양 황경차(-180~+180)"""
    return (_ecl_lon_moon(dt_utc) - _ecl_lon_sun(dt_utc) + 180.0) % 360.0 - 180.0


def _bisect_new_moon(t0_utc: datetime, t1_utc: datetime, tol_seconds: int = 1) -> datetime:
    """합삭 시각을 이분법으로 탐색"""
    f0 = _elongation(t0_utc)
    f1 = _elongation(t1_utc)
    for _ in range(100):
        if abs((t1_utc - t0_utc).total_seconds()) <= tol_seconds:
            return t0_utc
        mid = t0_utc + (t1_utc - t0_utc) / 2
        fm = _elongation(mid)
        if (f0 <= 0 < fm) or (fm <= 0 < f0):
            t1_utc, f1 = mid, fm
        else:
            t0_utc, f0 = mid, fm
    return t0_utc


# -----------------------
# 합삭 & 중기 리스트
# -----------------------
def list_new_moons(year: int) -> List[Dict[str, Any]]:
    """해당 연도 전후 버퍼 포함 새달(합삭) 목록 반환"""
    start_utc = datetime(year - 1, 12, 15, tzinfo=timezone.utc)
    end_utc = datetime(year + 1, 3, 1, tzinfo=timezone.utc)
    res: List[Dict[str, Any]] = []
    step = timedelta(hours=6)

    t0 = start_utc
    f0 = _elongation(t0)
    t = t0 + step
    while t <= end_utc:
        f = _elongation(t)
        if (f0 <= 0 < f) or (f <= 0 < f0) or abs(f) < 1e-3:
            nm = _bisect_new_moon(t - step, t)
            res.append({"time_utc": nm, "time_kst": nm.astimezone(KST)})
            t = nm + timedelta(hours=12)
            f0 = _elongation(t)
            t += step
            continue
        f0 = f
        t += step

    res.sort(key=lambda x: x["time_utc"])
    return res


def _principal_terms(year: int) -> List[Dict[str, Any]]:
    """전/현/익년 중기 합쳐 반환"""
    pts: List[Dict[str, Any]] = []
    for y in (year - 1, year, year + 1):
        pts += get_principal_terms(y)
    out: List[Dict[str, Any]] = []
    for p in pts:
        out.append({
            "degree": int(p["degree"]),
            "time_utc": datetime.fromisoformat(p["time_utc"]).replace(tzinfo=timezone.utc),
        })
    out.sort(key=lambda x: x["time_utc"])
    return out


# -----------------------
# 음력월 할당
# -----------------------
def _assign_lunar_months(year: int) -> List[Dict[str, Any]]:
    """
    동지(λ☉=270°)를 포함하는 달을 음력 11월로 삼아 월번호를 부여한다.
    - 자료 범위: 전년 11월 ~ 익년 3월까지 넉넉히 커버
    - 각 음력월 구간(합삭~다음 합삭) 내에 '중기(0,30,...330°)' 존재 여부로 윤달 판단
    """
    # 1) 합삭 목록(전년 11/01 ~ 익년 03/01 버퍼)
    start_buf = datetime(year - 1, 11, 1, tzinfo=timezone.utc)
    end_buf   = datetime(year + 1, 3, 1, tzinfo=timezone.utc)
    newmoons_all = list_new_moons(year)  # 이미 전년 12/15~익년 3/1 커버 → 살짝 부족할 수 있어 보강
    # 필요시 앞/뒤 추가 스캔
    if newmoons_all[0]["time_utc"] > start_buf:
        extra = list_new_moons(year - 1)
        newmoons_all = extra + newmoons_all
    if newmoons_all[-1]["time_utc"] < end_buf:
        extra = list_new_moons(year + 1)
        newmoons_all = newmoons_all + extra

    # 2) 중기(전/현/익년) 목록
    pts = _principal_terms(year)

    # 3) 동지 시각(λ☉=270°) 찾기
    dongji = None
    for p in pts:
        if int(p["degree"]) == 270:
            dongji = p["time_utc"]  # UTC
            break
    if dongji is None:
        # 안전 폴백: 가장 가까운 270°를 선택
        candidates = [p for p in pts if int(p["degree"]) == 270]
        if candidates:
            dongji = min(candidates, key=lambda x: abs((x["time_utc"] - datetime(year,12,21,tzinfo=timezone.utc)).total_seconds()))["time_utc"]
        else:
            raise RuntimeError("동지(270°)를 찾을 수 없습니다.")

    # 4) 동지 직전 또는 직후의 합삭 찾기: 동지를 '포함'하는 음력월을 11월로
    idx_11 = None
    for i in range(len(newmoons_all) - 1):
        if newmoons_all[i]["time_utc"] <= dongji < newmoons_all[i+1]["time_utc"]:
            idx_11 = i
            break
    if idx_11 is None:
        # 경계 폴백
        idx_11 = 0

    # 5) 합삭→월 구간 만들기
    months: List[Dict[str, Any]] = []
    for i in range(len(newmoons_all) - 1):
        start_utc = newmoons_all[i]["time_utc"]
        end_utc   = newmoons_all[i+1]["time_utc"]
        m: Dict[str, Any] = {
            "start_utc": start_utc,
            "end_utc": end_utc,
            "start_kst": start_utc.astimezone(KST),
            "end_kst": end_utc.astimezone(KST),
            "has_principal": False,
            "leap": False,
            "month_no": None,
        }
        # 구간 내 중기 존재 여부
        for p in pts:
            if start_utc <= p["time_utc"] < end_utc:
                m["has_principal"] = True
                break
        months.append(m)

    # 6) 동지를 포함하는 달을 '11월'로 부여, 이후 순차 증분
    #    (윤달: 중기 없음 → 같은 번호 유지)
    # 앞으로(11→12→1→…)
    num = 11
    for i in range(idx_11, len(months)):
        if months[i]["month_no"] is not None:
            continue
        if months[i]["has_principal"]:
            months[i]["leap"] = False
            months[i]["month_no"] = num
            num = 12 if num == 11 else (1 if num == 12 else num + 1)
        else:
            months[i]["leap"] = True
            months[i]["month_no"] = num  # 같은 번호(윤달)

    # 뒤로(10→9→8→…)
    num = 10
    for i in range(idx_11 - 1, -1, -1):
        if months[i]["month_no"] is not None:
            continue
        if months[i]["has_principal"]:
            months[i]["leap"] = False
            months[i]["month_no"] = num
            num = 9 if num == 10 else (12 if num == 1 else num - 1)
        else:
            months[i]["leap"] = True
            months[i]["month_no"] = num  # 같은 번호(윤달)

    # 관심 연도(KST 기준) 월만 대체로 쓰지만, 범위는 넉넉히 유지
    return months



# -----------------------
# 공개 API
# -----------------------
def to_lunar(dt: datetime) -> Dict[str, Any]:
    """
    KST 기준 양력 datetime -> 음력 날짜/윤달 반환
    - 동지-기준 월번호 부여 테이블 기반
    - 라운드트립(→ lunar_to_solar) 시 KST 시간 보존
    """
    dt_kst = dt if dt.tzinfo else KST.localize(dt)
    # 동지가 걸리는 '양력 연도'를 기준으로 테이블 구성
    months = _assign_lunar_months(dt_kst.year)

    # dt가 속한 음력월 찾기
    dt_utc = dt_kst.astimezone(timezone.utc)
    target = None
    for m in months:
        if m["start_utc"] <= dt_utc < m["end_utc"]:
            target = m
            break
    if target is None:
        # 경계면 이웃 연도까지 시도
        for y in (dt_kst.year - 1, dt_kst.year + 1):
            months = _assign_lunar_months(y)
            for m in months:
                if m["start_utc"] <= dt_utc < m["end_utc"]:
                    target = m; break
            if target: break
    if target is None:
        return {"lunar_date": None, "leap": None, "meta": {"note": "boundary fallback"}}

    day = (dt_kst.date() - target["start_kst"].date()).days + 1
    # 음력 '연도'는 동지 기준으로 구간이 나뉘기 때문에,
    # 정월 이전 구간은 전년도표기를 쓸 수도 있지만, 실무에서는 '해당 정월' 기준을 많이 사용.
    # 여기서는 동지-기준 테이블의 자연스러운 연도를 사용(= target 시작 KST의 연도에서 보정)
    lunar_year = target["start_kst"].year if target["month_no"] in (11,12) and target["start_kst"].month == 12 else dt_kst.year

    return {
        "lunar_date": f"{int(lunar_year):04d}-{int(target['month_no']):02d}-{int(day):02d}",
        "leap": bool(target["leap"]),
        "meta": {
            "month_start": target["start_kst"].strftime("%Y-%m-%d %H:%M"),
            "has_principal": bool(target["has_principal"]),
        },
    }



if __name__ == "__main__":
    print(to_lunar(KST.localize(datetime(1966, 11, 4, 2, 5))))
def lunar_to_solar(lunar_year: int, lunar_month: int, lunar_day: int, hour: int, minute: int, leap: bool = False):
    """
    음력 (년-월-일, 윤달여부, KST 시분) -> 양력 datetime(KST)
    - korean_lunar_calendar 패키지를 사용해 정확한 변환 수행
    - KST '시간' 보존
    """
    try:
        from korean_lunar_calendar import KoreanLunarCalendar
    except Exception as e:
        return {
            "solar_kst": None,
            "solar_str": None,
            "meta": {"note": f"korean-lunar-calendar 패키지 로드 실패: {e}"}
        }

    kcal = KoreanLunarCalendar()
    ok = kcal.setLunarDate(int(lunar_year), int(lunar_month), int(lunar_day), bool(leap))
    if not ok:
        return {
            "solar_kst": None,
            "solar_str": None,
            "meta": {"note": f"유효하지 않은 음력 날짜: {lunar_year}-{lunar_month:02d}-{lunar_day:02d} (leap={leap})"}
        }

    solar_iso = (kcal.SolarIsoFormat() or "").split()[0].strip()
    if len(solar_iso) != 10:
        return {
            "solar_kst": None,
            "solar_str": None,
            "meta": {"note": "음력→양력 변환 결과를 읽을 수 없습니다."}
        }

    sy, sm, sd = [int(x) for x in solar_iso.split("-")]
    solar_kst = KST.localize(datetime(sy, sm, sd, int(hour), int(minute)))

    return {
        "solar_kst": solar_kst,
        "solar_str": solar_kst.strftime("%Y-%m-%d %H:%M"),
        "meta": {
            "month_start": solar_kst.replace(hour=0, minute=0).strftime("%Y-%m-%d %H:%M"),
            "has_principal": True,
            "leap": bool(leap),
        }
    }

   