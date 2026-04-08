# unteim/engine/lunar_kr.py
# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Optional, Union

# 표준 라이브러리: korean-lunar-calendar
# 설치: pip install korean-lunar-calendar
from korean_lunar_calendar import KoreanLunarCalendar

# pillars / luck 등과 동일 타임존 (pytz: localize() 지원)
import pytz

KST = pytz.timezone("Asia/Seoul")

DateLike = Union[date, datetime, str]


def _to_date(dt: DateLike) -> Optional[date]:
    if isinstance(dt, date) and not isinstance(dt, datetime):
        return dt
    if isinstance(dt, datetime):
        return dt.date()
    if isinstance(dt, str):
        s = dt.strip()
        # "YYYY-MM-DD HH:MM" 또는 "YYYY-MM-DD"
        try:
            if len(s) >= 16:
                return datetime.strptime(s[:16], "%Y-%m-%d %H:%M").date()
            return datetime.strptime(s[:10], "%Y-%m-%d").date()
        except Exception:
            return None
    return None


def solar_to_lunar(dt: DateLike) -> Optional[Dict[str, Any]]:
    """
    양력 -> 음력 변환 (한국식)
    반환 예:
      {
        "y": 1966, "m": 9, "d": 22,
        "is_leap": False,
        "lunar_date": "1966-09-22"
      }
    """
    d = _to_date(dt)
    if d is None:
        return None

    cal = KoreanLunarCalendar()
    # 중요: setSolarDate는 (y, m, d)
    cal.setSolarDate(d.year, d.month, d.day)

    ly = int(cal.lunarYear)
    lm = int(cal.lunarMonth)
    ld = int(cal.lunarDay)
    is_leap = bool(cal.isIntercalation)

    return {
        "y": ly,
        "m": lm,
        "d": ld,
        "is_leap": is_leap,
        "lunar_date": f"{ly:04d}-{lm:02d}-{ld:02d}",
    }
