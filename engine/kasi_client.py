# unteim/engine/kasi_client.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from zoneinfo import ZoneInfo

# KASI 단독 호출(양력 -> 음력)
from .kasi_api_adapter import call_kasi_lunar_api, KasiApiError
from .month_branch_resolver import TERM_TO_BRANCH
from .solar_terms_loader import SolarTermsLoader

KST = ZoneInfo("Asia/Seoul")
SOLAR_TERM_TO_BRANCH = TERM_TO_BRANCH
MONTH_BOUNDARY_TERMS: List[str] = [
    "입춘",
    "경칩",
    "청명",
    "입하",
    "망종",
    "소서",
    "입추",
    "백로",
    "한로",
    "입동",
    "대설",
    "소한",
]

_solar_loader = SolarTermsLoader()


@dataclass(frozen=True)
class SolarTermProbe:
    """fetch_solarterm() 반환: 날짜 근접 절기(로컬 계산)."""

    term_name: str
    term_datetime: str


def fetch_solarterm(date_str: str) -> SolarTermProbe:
    """
    YYYY-MM-DD 기준 해당 시점 직전 절입 정보(로컬 SolarTermsLoader).
    tools/seed_year_terms.py 호환 — 외부 KASI 절기 API 대신 내부 역학 데이터 사용.
    """
    try:
        dt0 = datetime.strptime(date_str.strip(), "%Y-%m-%d")
    except ValueError:
        return SolarTermProbe(term_name="", term_datetime="")
    dt_kst = datetime(dt0.year, dt0.month, dt0.day, 12, 0, 0, tzinfo=KST)
    term = _solar_loader.find_last_term_before(dt_kst)
    if term is None:
        return SolarTermProbe(term_name="", term_datetime="")
    return SolarTermProbe(term_name=term.name, term_datetime=term.dt_kst.isoformat())


@dataclass(frozen=True)
class NextSolarTerm:
    """get_next_solar_term_after() 반환: 다음 절입 시각(KST)."""

    timestamp_kst: datetime


def get_solar_terms_for_year(year: int) -> Dict[str, datetime]:
    """연도별 절기명 → KST datetime (daewoonCalculator / luckTimeline 호환)."""
    terms = _solar_loader.get_terms_for_year(year)
    return {name: item.dt_kst for name, item in terms.items()}


def get_next_solar_term_after(dt_kst: datetime) -> NextSolarTerm:
    """dt_kst 이후 첫 절입 시각."""
    if dt_kst.tzinfo is None:
        dt_kst = dt_kst.replace(tzinfo=KST)
    else:
        dt_kst = dt_kst.astimezone(KST)
    y = dt_kst.year
    pairs: List[Tuple[datetime, str]] = []
    for yy in (y - 1, y, y + 1, y + 2):
        for item in _solar_loader.get_terms_for_year(yy).values():
            pairs.append((item.dt_kst, item.name))
    pairs.sort(key=lambda x: x[0])
    for t, _name in pairs:
        if t > dt_kst:
            return NextSolarTerm(timestamp_kst=t)
    raise RuntimeError("get_next_solar_term_after: no term after dt_kst")


def _month_boundary_pairs(dt_kst: datetime) -> List[Tuple[datetime, str]]:
    """월주 경계에 쓰는 12절(節)만 모은 뒤 시각순 정렬."""
    if dt_kst.tzinfo is None:
        dt_kst = dt_kst.replace(tzinfo=KST)
    else:
        dt_kst = dt_kst.astimezone(KST)
    y = dt_kst.year
    pairs: List[Tuple[datetime, str]] = []
    # 12절만 필요; 생일 연도 ±1이면 충분(y+2는 미보강 연도에서 불필요한 astropy 재계산을 유발)
    for yy in (y - 1, y, y + 1):
        for item in _solar_loader.get_terms_for_year(yy).values():
            if item.name in MONTH_BOUNDARY_TERMS:
                pairs.append((item.dt_kst, item.name))
    pairs.sort(key=lambda x: x[0])
    return pairs


def get_next_month_boundary_after(dt_kst: datetime) -> NextSolarTerm:
    """대운 起運(순행): 생시 이후 첫 12절(월의 절) 시각."""
    for t, _name in _month_boundary_pairs(dt_kst):
        if t > dt_kst:
            return NextSolarTerm(timestamp_kst=t)
    raise RuntimeError("get_next_month_boundary_after: no month boundary after dt_kst")


def get_prev_month_boundary_on_or_before(dt_kst: datetime) -> NextSolarTerm:
    """대운 起運(역행): 생시 이전(또는 동시) 마지막 12절 시각."""
    last: Optional[datetime] = None
    for t, _name in _month_boundary_pairs(dt_kst):
        if t <= dt_kst:
            last = t
        else:
            break
    if last is None:
        raise RuntimeError("get_prev_month_boundary_on_or_before: no month boundary on/before dt_kst")
    return NextSolarTerm(timestamp_kst=last)


@dataclass(frozen=True)
class LunarDate:
    """
    음력 날짜(윤달 여부 포함)
    - year, month, day: 음력 기준
    - is_leap: 윤달 여부
    """
    year: int
    month: int
    day: int
    is_leap: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return {"year": self.year, "month": self.month, "day": self.day, "is_leap": self.is_leap}


def _ensure_datetime(dt: datetime) -> datetime:
    if not isinstance(dt, datetime):
        raise TypeError(f"dt must be datetime, got {type(dt)}")
    return dt


def kasi_solar_to_lunar(dt: datetime, timeout_sec: float = 7.0) -> Dict[str, Any]:
    """
    ✅ KASI 기반 양력 -> 음력 변환 (datetime 입력)
    반환: {"year": int, "month": int, "day": int, "is_leap": bool}

    - timing_engine / sajuCalculator에서 바로 쓰기 좋도록 dict로 통일
    """
    dt = _ensure_datetime(dt)
    return call_kasi_lunar_api(year=dt.year, month=dt.month, day=dt.day, timeout_sec=timeout_sec)


def kasi_solar_to_lunar_obj(dt: datetime, timeout_sec: float = 7.0) -> LunarDate:
    """
    양력 -> 음력 변환 결과를 LunarDate 객체로 반환
    """
    out = kasi_solar_to_lunar(dt, timeout_sec=timeout_sec)
    return LunarDate(
        year=int(out["year"]),
        month=int(out["month"]),
        day=int(out["day"]),
        is_leap=bool(out.get("is_leap", False)),
    )


def kasi_solar_to_lunar_tuple(dt: datetime, timeout_sec: float = 7.0) -> Tuple[int, int, int, bool]:
    """
    양력 -> 음력 변환 결과를 (year, month, day, is_leap) 튜플로 반환
    """
    out = kasi_solar_to_lunar(dt, timeout_sec=timeout_sec)
    return int(out["year"]), int(out["month"]), int(out["day"]), bool(out.get("is_leap", False))


def safe_kasi_solar_to_lunar(dt: datetime, timeout_sec: float = 1.2) -> Optional[Dict[str, Any]]:
    """
    ✅ 실패해도 서비스가 죽지 않게 하는 안전 래퍼
    - 성공 시 dict 반환
    - 실패 시 None 반환
    """
    dt = _ensure_datetime(dt)
    try:
        return kasi_solar_to_lunar(dt, timeout_sec=timeout_sec)
    except KasiApiError:
        return None
    except Exception:
        return None
    
# =========================
# KASI / Skyfield solar terms (year)
# =========================

from .astro_solar_terms import compute_solar_terms_for_year


def fetch_kasi_data(year: int) -> List[Dict[str, Any]]:
    """
    연간 24절기 데이터를 반환합니다.
    - 내부 구현은 astro_solar_terms.compute_solar_terms_for_year()를 사용합니다.
    - seed_year_terms.py가 JSON으로 저장할 수 있도록 list[dict] 형태로 변환합니다.
    """

    terms = compute_solar_terms_for_year(year)
    print("[DEBUG] terms type =", type(terms))
    try:
        print("[DEBUG] terms len =", len(terms))
    except Exception as e:
        print("[DEBUG] terms len error =", e)

    out: List[Dict[str, Any]] = []
    for i, t in enumerate(terms, start=1):
        # t가 dataclass(SolarTerm)일 가능성이 높음
        # name / dt 같은 필드명이 다를 수 있어 안전하게 처리
        name = getattr(t, "name", None)

        # astro_solar_terms.SolarTerm의 실제 datetime 필드
        dt = getattr(t, "dt_kst", None)

        if isinstance(dt, datetime):
            dt_iso = dt.isoformat()
            date_iso = dt.date().isoformat()
        else:
            # 혹시 문자열이거나 None이면 그대로 처리
            dt_iso = str(dt) if dt is not None else None
            date_iso = None

        out.append({
            "name": name,
            "year": year,
            "index": i,
            "date": date_iso,     # 날짜(YYYY-MM-DD)
            "dt": dt_iso          # 날짜+시간(ISO) 가능하면 포함
        })

    return out
