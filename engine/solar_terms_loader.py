from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from typing import Dict, List, Optional, Iterable

KST = ZoneInfo("Asia/Seoul")

# ✅ 오슈님 파일 경로(지금 올려준 위치 기준)
# 파일명이 다르면 여기만 바꾸면 됩니다.
DEFAULT_CSV_PATH = Path(__file__).parent / "data" / "solar_terms_cache.csv"


@dataclass(frozen=True)
class SolarTerm:
    name: str          # 절기명 (예: 입춘)
    dt: datetime       # KST-aware datetime
    year: int          # 파일의 기준 연도(행 첫 컬럼)


def load_solar_terms_csv(csv_path: Path = DEFAULT_CSV_PATH) -> List[SolarTerm]:
    """
    CSV 한 줄 예시(캡쳐 기준):
    2026,소한,285.0,2026-01-05 17:23:09,2026-01-05 08:23:09,285.000003...
                 ^^^^^^^^^^^^^^^^^^^^^^^
                 우리가 쓰는 건 'KST 절입 시각' (4번째 컬럼)
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"solar terms csv not found: {csv_path}")

    out: List[SolarTerm] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:

        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            # 안전장치: 헤더가 있으면 스킵
            row[0] = row[0].replace("\ufeff", "").strip()
            if row[0].strip().lower() in ("year", "y"):
                continue

            year = int(row[0].strip())
            name = row[1].strip()

            kst_str = row[3].strip()  # ⭐ KST 절입 시각
            dt = datetime.strptime(kst_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=KST)

            out.append(SolarTerm(name=name, dt=dt, year=year))

    # 절입 시각 기준으로 정렬 (절대 필수)
    out.sort(key=lambda x: x.dt)
    return out


def filter_terms_around(dt_kst: datetime, terms: Iterable[SolarTerm]) -> List[SolarTerm]:
    """
    dt_kst 주변 연도만 쓰고 싶을 때(속도 최적화)
    - 월주 절입 비교는 연초 경계 때문에 year-1 ~ year+1 정도면 충분
    """
    y = dt_kst.year
    return [t for t in terms if (y - 1) <= t.dt.year <= (y + 1)]


def find_last_term_before(dt_kst: datetime, terms_sorted: List[SolarTerm]) -> Optional[SolarTerm]:
    """
    dt_kst 이전(<=)인 가장 마지막 절기를 반환
    """
    last = None
    for t in terms_sorted:
        if t.dt <= dt_kst:
            last = t
        else:
            break
    return last


# -----------------------------
# ✅ 기존 코드 호환을 위한 "래퍼"
# (다른 파일이 기존 함수명을 부르고 있을 가능성 대비)
# -----------------------------

_TERMS_CACHE: Optional[List[SolarTerm]] = None

def get_terms_cached(csv_path: Path = DEFAULT_CSV_PATH) -> List[SolarTerm]:
    global _TERMS_CACHE
    if _TERMS_CACHE is None:
        _TERMS_CACHE = load_solar_terms_csv(csv_path)
    return _TERMS_CACHE


def get_terms_for_datetime(dt_kst: datetime, csv_path: Path = DEFAULT_CSV_PATH) -> List[SolarTerm]:
    terms = get_terms_cached(csv_path)
    return filter_terms_around(dt_kst, terms)

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Optional

from .solar_terms import find_term_times  # ✅ 방금 통째 교체한 solar_terms.py 사용

KST = ZoneInfo("Asia/Seoul")


@dataclass(frozen=True)
class SolarTermItem:
    name: str
    degree: int
    dt_kst: datetime
    dt_utc: datetime


class SolarTermsLoader:
    """
    month_branch_resolver.py 호환용 Loader
    - 내부 데이터 소스는 solar_terms.py(=CSV cache single source)
    """

    def __init__(self):
        pass

    def get_terms_for_year(self, year: int) -> Dict[str, SolarTermItem]:
        """
        return: { '입춘': SolarTermItem(...), ... }
        """
        rows = find_term_times(year)  # 24절기
        out: Dict[str, SolarTermItem] = {}

        for r in rows:
            name = r["name"]
            deg = int(r["degree"])
            dt_utc = datetime.fromisoformat(r["time_utc"].replace("Z", "+00:00"))
            dt_kst = datetime.fromisoformat(r["time_kst"])
            if dt_kst.tzinfo is None:
                dt_kst = dt_kst.replace(tzinfo=KST)

            out[name] = SolarTermItem(
                name=name,
                degree=deg,
                dt_kst=dt_kst,
                dt_utc=dt_utc,
            )

        return out
   
     # ✅ MonthBranchResolver 호환: 기존 이름 alias
    def get_year_terms(self, year: int) -> Dict[str, str]:
        """
        month_branch_resolver.py가 기대하는 형태:
        { '입춘': '2026-02-04T05:02:07+09:00', ... }  (ISO 문자열)
        """
        terms = self.get_terms_for_year(year)  # Dict[str, SolarTermItem]
        return {name: item.dt_kst.isoformat() for name, item in terms.items()}

    def find_last_term_before(self, dt_kst: datetime) -> Optional[SolarTermItem]:
        """
        dt_kst 직전(<=) 절기(24절기 기준) 중 가장 마지막을 반환
        """
        if dt_kst.tzinfo is None:
            dt_kst = dt_kst.replace(tzinfo=KST)

        y = dt_kst.year
        candidates = []
        for yy in (y - 1, y, y + 1):
            terms = self.get_terms_for_year(yy)
            candidates.extend(list(terms.values()))

        candidates.sort(key=lambda x: x.dt_kst)

        last = None
        for t in candidates:
            if t.dt_kst <= dt_kst:
                last = t
            else:
                break
        return last
    def find_adjacent_principal_term_name(self, dt_kst: datetime) -> Optional[str]:
        """
        wolwoon_engine 호환용:
        기준 시점(dt_kst) 직전에 위치한 절기의 name(문자열) 반환
        """
        term = self.find_last_term_before(dt_kst)
        return term.name if term else None

    def find_adjacent_principal_term(self, dt_kst: datetime) -> Optional[datetime]:
        """
        (옵션) 기준 시점 직전 절기의 datetime(KST) 반환
        """
        term = self.find_last_term_before(dt_kst)
        return term.dt_kst if term else None

    