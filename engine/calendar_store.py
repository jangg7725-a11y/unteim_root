# unteim/engine/calendar_store.py
from __future__ import annotations
import os, sqlite3
from typing import List, Dict, Any, Tuple
from datetime import date, datetime
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

# DB 기본 경로: 엔진/데이터 폴더
DEFAULT_DB = os.path.join(os.path.dirname(__file__), "data", "calendar.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS solar_terms (
  year INTEGER NOT NULL,
  name TEXT NOT NULL,
  kst TEXT NOT NULL,            -- 'YYYY-MM-DD HH:MM:SS' (KST)
  ecliptic_deg REAL,            -- 태양 황경(옵션)
  PRIMARY KEY (year, name)
);
"""

def open_db(db_path: str | None = None) -> sqlite3.Connection:
    path = db_path or DEFAULT_DB
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute(SCHEMA_SQL)
    return conn

def upsert_terms(conn: sqlite3.Connection, year: int, terms: List[Dict[str, Any]]) -> None:
    # terms: [{"name":"입춘","kst":"2025-02-03 17:10:00","ecliptic_deg":315.0}, ...]
    cur = conn.cursor()
    for t in terms:
        cur.execute(
            "INSERT INTO solar_terms(year,name,kst,ecliptic_deg) VALUES(?,?,?,?) "
            "ON CONFLICT(year,name) DO UPDATE SET kst=excluded.kst, ecliptic_deg=excluded.ecliptic_deg",
            (year, t["name"], t["kst"], float(t.get("ecliptic_deg") or 0.0)),
        )
    conn.commit()

def fetch_year_terms(conn: sqlite3.Connection, year: int) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT name,kst,ecliptic_deg FROM solar_terms WHERE year=? ORDER BY kst ASC", (year,)
    ).fetchall()
    return [{"name": r[0], "kst": r[1], "ecliptic_deg": r[2]} for r in rows]

def get_or_compute_terms(year: int, compute_fn, db_path: str | None = None) -> List[Dict[str, Any]]:
    """
    compute_fn(year:int)->List[term dict] 를 받아 캐시 조회 후 없으면 계산→저장→반환.
    """
    conn = open_db(db_path)
    rows = fetch_year_terms(conn, year)
    if rows:
        return rows
    # 미존재 → 계산
    terms = compute_fn(year)
    if not terms:
        return []
    upsert_terms(conn, year, terms)
    return terms


def init_schema(db_path: str | None = None) -> None:
    """SQLite 스키마 보장(테이블 생성). tools/seed_year_terms.py 호환."""
    conn = open_db(db_path)
    conn.close()


def _iso_to_kst_sql(iso_kst: str) -> str:
    """ISO(+09:00 등) → DB 컬럼용 'YYYY-MM-DD HH:MM:SS' (KST)."""
    s = (iso_kst or "").strip()
    if not s:
        return ""
    try:
        if s.endswith("Z"):
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=KST)
        else:
            dt = dt.astimezone(KST)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return s[:19] if len(s) >= 19 else s


def upsert_solar_term(year: int, name: str, iso_kst: str, db_path: str | None = None) -> None:
    """단일 절기 upsert. iso_kst는 ISO 문자열."""
    kst = _iso_to_kst_sql(iso_kst)
    if not name or not kst:
        return
    conn = open_db(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO solar_terms(year,name,kst,ecliptic_deg) VALUES(?,?,?,?) "
            "ON CONFLICT(year,name) DO UPDATE SET kst=excluded.kst, ecliptic_deg=excluded.ecliptic_deg",
            (year, name, kst, 0.0),
        )
        conn.commit()
    finally:
        conn.close()


def get_solar_terms(year: int, db_path: str | None = None) -> List[Tuple[str, str]]:
    """(절기명, KST 문자열) 목록."""
    conn = open_db(db_path)
    try:
        rows = fetch_year_terms(conn, year)
        return [(r["name"], r["kst"]) for r in rows]
    finally:
        conn.close()
