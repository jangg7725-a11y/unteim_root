# unteim/engine/month_term_resolver.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
from zoneinfo import ZoneInfo
import json

KST = ZoneInfo("Asia/Seoul")

# 월주 절입(12절입) 기준: 이 12개만 경계로 사용
JEOLIP_NAMES = [
    "입춘", "경칩", "청명", "입하", "망종", "소서",
    "입추", "백로", "한로", "입동", "대설", "소한",
]


def _load_terms_cache() -> Dict[str, Any]:
    """
    data/solar_terms_cache_kst.json 로딩
    구조(당신 캡쳐 기준):
    {
      "meta": {...},
      "years": {
        "2026": { "입춘": "2026-02-04T05:02:07+09:00", ... }
      }
    }
    """
    here = Path(__file__).resolve().parent
    p = here / "data" / "solar_terms_cache_kst.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _parse_dt_kst(s: str) -> Optional[datetime]:
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=KST)
        else:
            dt = dt.astimezone(KST)
        return dt
    except Exception:
        return None


def _collect_year_jeolip(year_block: Dict[str, str]) -> List[Tuple[str, datetime]]:
    out: List[Tuple[str, datetime]] = []
    for name in JEOLIP_NAMES:
        iso = year_block.get(name)
        if not iso:
            continue
        dt = _parse_dt_kst(iso)
        if dt:
            out.append((name, dt))
    out.sort(key=lambda x: x[1])
    return out


def resolve_month_term(dt_kst: datetime) -> Tuple[Optional[str], Optional[datetime]]:
    """
    dt_kst 직전(<=)의 '절입(12절입)'을 찾아 반환
    반환: (month_term_name, month_term_dt_kst)
    """
    if dt_kst.tzinfo is None:
        dt_kst = dt_kst.replace(tzinfo=KST)
    else:
        dt_kst = dt_kst.astimezone(KST)

    cache = _load_terms_cache()
    years = cache.get("years")
    if not isinstance(years, dict):
        return None, None

    y = str(dt_kst.year)
    y_prev = str(dt_kst.year - 1)

    # 후보: 올해 + (필요시) 전년도까지
    candidates: List[Tuple[str, datetime]] = []

    block = years.get(y)
    if isinstance(block, dict):
        candidates.extend(_collect_year_jeolip(block))

    block_prev = years.get(y_prev)
    if isinstance(block_prev, dict):
        candidates.extend(_collect_year_jeolip(block_prev))

    if not candidates:
        return None, None

    candidates.sort(key=lambda x: x[1])

    last_name = None
    last_dt = None
    for name, t in candidates:
        if t <= dt_kst:
            last_name, last_dt = name, t
        else:
            break

    return last_name, last_dt
