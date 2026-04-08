# -*- coding: utf-8 -*-
"""
solar_terms.py (CSV cache single source of truth)

- 소스: solar_terms_cache.csv (아래 순으로 탐색)
    1) engine/data/solar_terms_cache.csv
    2) 프로젝트 루트 data/solar_terms_cache.csv
  (컬럼 예: year,name,angle_deg,time_kst,time_utc,longitude_deg)
- 제공:
  * get_principal_terms(year): 중기(30°) 12개
  * find_term_times(year): 24절기(15°) 24개
  * find_adjacent_principal_terms(dt): dt 기준 직전/직후 중기
  * apply_solar_term_correction(dt): 월주 보정 메타
  * month_branch_index(dt_kst): (호환) 중기 인덱스 0~11
  * is_before_ipchun_kst(dt_kst): (호환) 입춘(315°) 이전 여부
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from zoneinfo import ZoneInfo
    KST = ZoneInfo("Asia/Seoul")
except Exception:
    KST = None  # type: ignore


_ENGINE_DIR = Path(__file__).resolve().parent


def _resolve_csv_path() -> Path:
    """engine/data 우선, 없으면 저장소 루트 data/ (기존 배치 호환)."""
    candidates = (
        _ENGINE_DIR / "data" / "solar_terms_cache.csv",
        _ENGINE_DIR.parent / "data" / "solar_terms_cache.csv",
    )
    for p in candidates:
        if p.is_file():
            return p
    return candidates[0]


CSV_PATH = _resolve_csv_path()
DATA_DIR = CSV_PATH.parent


@dataclass(frozen=True)
class TermRow:
    year: int
    name: str
    degree: int
    time_kst: datetime
    time_utc: datetime


_TERMS_BY_YEAR: Optional[Dict[int, List[TermRow]]] = None


def _load_all_terms() -> Dict[int, List[TermRow]]:
    """
    CSV를 한 번만 읽어서 연도별로 캐시.
    BOM(\ufeff) 문제 방지: utf-8-sig 사용.
    """
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"[solar_terms] CSV cache not found: {CSV_PATH}")

    by_year: Dict[int, List[TermRow]] = {}

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue

            # 헤더/이상치 스킵
            c0 = (row[0] or "").replace("\ufeff", "").strip()
            if c0.lower() in ("year", "y"):
                continue

            # 캡쳐 기준: [0]=year, [1]=name, [2]=degree, [3]=time_kst, [4]=time_utc
            try:
                year = int(c0)
                name = (row[1] or "").strip()
                degree = int(float(row[2]))  # 315.0 같은 값 대응
                kst_str = (row[3] or "").strip()
                utc_str = (row[4] or "").strip()
            except Exception:
                continue

            if not name or not kst_str or not utc_str:
                continue

            dt_kst = datetime.strptime(kst_str, "%Y-%m-%d %H:%M:%S")
            dt_utc = datetime.strptime(utc_str, "%Y-%m-%d %H:%M:%S")

            # tz 부여
            if KST is not None:
                dt_kst = dt_kst.replace(tzinfo=KST)
            else:
                dt_kst = dt_kst.replace(tzinfo=timezone.utc)  # fallback

            dt_utc = dt_utc.replace(tzinfo=timezone.utc)

            tr = TermRow(year=year, name=name, degree=degree, time_kst=dt_kst, time_utc=dt_utc)
            by_year.setdefault(year, []).append(tr)

    # 연도별 시간순 정렬
    for y in list(by_year.keys()):
        by_year[y].sort(key=lambda x: x.time_utc)

    return by_year


def _ensure_cache() -> Dict[int, List[TermRow]]:
    global _TERMS_BY_YEAR
    if _TERMS_BY_YEAR is None:
        _TERMS_BY_YEAR = _load_all_terms()
    return _TERMS_BY_YEAR


def find_term_times(year: int) -> List[Dict[str, str]]:
    """
    24절기 전체(0,15,...,345) 반환
    반환 포맷은 기존 compute/fixed 스타일과 최대한 맞춤:
      [{"degree":"315","time_utc":"...Z","name":"입춘", "time_kst":"..."}]
    """
    db = _ensure_cache()
    rows = db.get(year, [])
    if not rows:
        raise RuntimeError(f"[solar_terms] no terms for year={year} in CSV cache")

    out: List[Dict[str, str]] = []
    for r in rows:
        out.append({
            "degree": str(int(r.degree)),
            "name": r.name,
            "time_utc": r.time_utc.isoformat().replace("+00:00", "Z"),
            "time_kst": r.time_kst.isoformat(),
        })
    return out


def get_principal_terms(year: Union[int, date, datetime, str]) -> List[Dict[str, str]]:
    """
    중기(30°) 12개 반환.
    (0,30,...,330)
    """
    # year 정규화 (date / datetime / "YYYY-MM-DD" 대비)
    if isinstance(year, (date, datetime)):
        y = year.year
    else:
        y = int(str(year)[:4])
    year = y

    terms = find_term_times(year)
    pts = [t for t in terms if int(t["degree"]) % 30 == 0]
    if len(pts) < 10:
        raise RuntimeError(f"[solar_terms] principal terms too few for year={year}")
    return pts


def find_adjacent_principal_terms(dt: datetime) -> Dict[str, Any]:
    """
    dt(UTC 또는 tz-aware) 기준 직전/직후 중기
    반환:
      {"input": iso, "prev_term": {"degree":..,"time_utc":..}|None, "next_term": ...|None}
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt_utc: datetime = dt.astimezone(timezone.utc)

    year = dt_utc.year
    pts: List[Dict[str, Any]] = []
    for y in (year - 1, year, year + 1):
        for t in get_principal_terms(y):
            pts.append({
                "degree": int(t["degree"]),
                "time_utc": datetime.fromisoformat(t["time_utc"].replace("Z", "+00:00")),
            })
    pts.sort(key=lambda x: x["time_utc"])

    prev_term: Optional[Dict[str, Any]] = None
    next_term: Optional[Dict[str, Any]] = None
    for t in pts:
        tt = t["time_utc"]
        if tt <= dt_utc:
            prev_term = t
        if tt > dt_utc:
            next_term = t
            break

    def pack(term: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not term:
            return None
        tu = term["time_utc"]
        tu_str = tu.isoformat() if isinstance(tu, datetime) else str(tu)
        return {
            "degree": int(term["degree"]),
            "time_utc": tu_str,
        }

    return {
        "input": dt_utc.isoformat(),
        "prev_term": pack(prev_term),
        "next_term": pack(next_term),
    }


def apply_solar_term_correction(dt: datetime) -> Dict[str, Any]:
    meta = find_adjacent_principal_terms(dt)
    prev_term = meta.get("prev_term")
    next_term = meta.get("next_term")
    month_anchor = prev_term["time_utc"] if prev_term else None
    return {"corrected": meta["input"], "month_anchor": month_anchor, "next_term": next_term}


# ──────────────────────────────
# 호환용 함수들
# ──────────────────────────────
def month_branch_index(dt_kst: datetime) -> int:
    """
    dt 기준 직전 중기의 degree를 0~11 인덱스로 변환:
      degree 0 → 0, 30 → 1, ..., 330 → 11
    """
    if dt_kst.tzinfo is None:
        # tz 없으면 KST로 가정
        if KST is not None:
            dt_kst = dt_kst.replace(tzinfo=KST)
        else:
            dt_kst = dt_kst.replace(tzinfo=timezone.utc)

    dt_utc = dt_kst.astimezone(timezone.utc)
    meta = find_adjacent_principal_terms(dt_utc)
    prev_term = meta.get("prev_term")
    if not prev_term:
        # 안전장치
        pts = get_principal_terms(dt_utc.year)
        prev_term = {
            "degree": int(pts[-1]["degree"]),
            "time_utc": datetime.fromisoformat(pts[-1]["time_utc"].replace("Z", "+00:00")),
        }

    degree = int(prev_term["degree"])
    return (degree // 30) % 12


def is_before_ipchun_kst(dt_kst: datetime) -> bool:
    """
    입춘(315°) 이전인지 여부 (KST 입력)
    """
    if dt_kst.tzinfo is None:
        if KST is not None:
            dt_kst = dt_kst.replace(tzinfo=KST)
        else:
            dt_kst = dt_kst.replace(tzinfo=timezone.utc)

    dt_utc = dt_kst.astimezone(timezone.utc)
    year = dt_utc.year

    terms = find_term_times(year)
    ipchun_utc: Optional[datetime] = None
    for t in terms:
        if int(t["degree"]) == 315:
            ipchun_utc = datetime.fromisoformat(t["time_utc"].replace("Z", "+00:00"))
            break

    if ipchun_utc is None:
        return False

    return dt_utc < ipchun_utc
