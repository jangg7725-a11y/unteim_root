# unteim/engine/timing_engine.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional, Tuple
from zoneinfo import ZoneInfo

import importlib


# =========================
# 내부 유틸
# =========================

def _month_range(d: date) -> Tuple[date, date]:
    """해당 월의 (첫날, 마지막날)"""
    first = d.replace(day=1)
    if first.month == 12:
        next_first = first.replace(year=first.year + 1, month=1)
    else:
        next_first = first.replace(month=first.month + 1)
    last = next_first - timedelta(days=1)
    return first, last


def _bucket_month_day(d: date) -> str:
    """이번 달 상/중/하순 라벨"""
    _, last = _month_range(d)
    if d.day <= 10:
        return "상순"
    if d.day <= 20:
        return "중순"
    # 마지막 10일이 아니어도 관습적으로 21~말일은 하순
    return "하순"


def _window_str(center: date, window_days: int = 3, calendar: str = "양력") -> str:
    """'N월 N일 전후 N일' 표기 (달력 표시 포함)"""
    return f"({calendar}) {center.month}월 {center.day}일 전후 {window_days}일"


def _normalize_lunar_output(out: Any) -> Optional[Tuple[int, int, int, bool]]:
    """
    여러 형태 반환을 (y,m,d,is_leap)로 normalize
    허용:
      - dict: year/month/day/is_leap or lunar_year/lunar_month/lunar_day/leap/윤달
      - tuple/list: (y,m,d) 또는 (y,m,d,is_leap)
      - dataclass/object: __dict__ 형태
    """
    if out is None:
        return None

    # dict
    if isinstance(out, dict):
        y = out.get("year") or out.get("lunar_year")
        m = out.get("month") or out.get("lunar_month")
        d = out.get("day") or out.get("lunar_day")
        is_leap = bool(out.get("is_leap") or out.get("leap") or out.get("윤달"))
        if y and m and d:
            return int(y), int(m), int(d), is_leap
        return None

    # tuple/list
    if isinstance(out, (tuple, list)) and len(out) >= 3:
        y, m, d = out[0], out[1], out[2]
        is_leap = bool(out[3]) if len(out) >= 4 else False
        if y and m and d:
            return int(y), int(m), int(d), is_leap
        return None

    # dataclass/object -> __dict__
    dd = getattr(out, "__dict__", None)
    if isinstance(dd, dict):
        y = dd.get("year") or dd.get("lunar_year")
        m = dd.get("month") or dd.get("lunar_month")
        d = dd.get("day") or dd.get("lunar_day")
        is_leap = bool(dd.get("is_leap") or dd.get("leap") or dd.get("윤달"))
        if y and m and d:
            return int(y), int(m), int(d), is_leap

    return None


def _fmt_lunar(y: int, m: int, d: int, is_leap: bool) -> str:
    """'음력 (윤)M월 D일 (Y)'"""
    leap = "윤" if is_leap else ""
    return f"음력 {leap}{m}월 {d}일 ({y})"


def _try_solar_to_lunar(d: date) -> Optional[Tuple[int, int, int, bool]]:
    """
    ✅ KASI 강제 사용 (양력 date -> 음력 (y,m,d,is_leap) 튜플)
    - 성공: (year, month, day, is_leap)
    - 실패: None  (서비스 안정성 유지)
    """
    try:
        from .kasi_client import safe_kasi_solar_to_lunar
    except Exception:
        return None

    if not isinstance(d, date):
        return None

    # date -> datetime(00:00) 래핑
    dt = datetime(d.year, d.month, d.day)

    out = safe_kasi_solar_to_lunar(dt)
    if not out:
        return None

    try:
        y = int(out["year"])
        m = int(out["month"])
        dd = int(out["day"])
        is_leap = bool(out.get("is_leap", False))
        return (y, m, dd, is_leap)
    except Exception:
        return None



def _pick_near_center(
    today: date,
    prefer_monthly: bool,
    prefer_yearly: bool,
) -> Tuple[str, date, int, str]:
    """
    결과: (precision_key, center_date, window_days, bucket)
    precision_key: "month" | "year" | "week"
    """
    if prefer_monthly:
        # 이번 달 중심(15~22 근처)에서 오늘과 가장 가까운 날짜를 중심으로
        _, last = _month_range(today)
        c1 = today.replace(day=min(15, last.day))
        c2 = today.replace(day=min(22, last.day))
        center = min([c1, c2], key=lambda x: abs((x - today).days)) + timedelta(days=2)
        return "month", center, 3, _bucket_month_day(center)

    if prefer_yearly:
        center = today + timedelta(days=30)
        return "year", center, 7, _bucket_month_day(center)

    center = today + timedelta(days=2)
    return "week", center, 2, _bucket_month_day(center)


# =========================
# 공개 API
# =========================

def refine_timing(
    today: date,
    has_daily_trigger: bool,
    has_monthly_trigger: bool,
    has_yearly_trigger: bool,
) -> Dict[str, Any]:
    """
    timing 판단 공개 API

    반환:
    {
        when, precision, window, calendar,
        why, suggestion,
        lunar: {year, month, day, is_leap} | None
    }
    """

    # -------------------------
    # 음력(KASI) 계산 (공통)
    # -------------------------
    lunar = _try_solar_to_lunar(today)

    lunar_dict = None
    if lunar:
        ly, lm, ld, is_leap = lunar
        lunar_dict = {
            "year": ly,
            "month": lm,
            "day": ld,
            "is_leap": is_leap,
        }

    # -------------------------
    # daily 트리거
    # -------------------------
    if has_daily_trigger:
        center = today
        window_days = 1
        why = "오늘은 흐름이 즉각적으로 반응하는 날입니다."
        suggestion = "중요한 결정은 빠르게 하되, 직감보다 사실 확인을 우선하세요."

        return {
            "when": "오늘",
            "precision": "일간",
            "window": _window_str(center, window_days, calendar="양력"),
            "calendar": "양력",
            "why": why,
            "suggestion": suggestion,
            "lunar": lunar_dict,
        }

    # -------------------------
    # monthly + yearly 트리거
    # -------------------------
    if has_monthly_trigger and has_yearly_trigger:
        bucket = _bucket_month_day(today)
        _, center, window_days, _ = _pick_near_center(
            today,
            prefer_monthly=True,
            prefer_yearly=True,
        )
        why = "월운과 연운이 동시에 작용하는 시기입니다."
        suggestion = "중요한 계획은 장기 관점에서 점검하세요."

        return {
            "when": f"이달 중 ({bucket})",
            "precision": "월간/연간",
            "window": _window_str(center, window_days, calendar="양력"),
            "calendar": "양력",
            "why": why,
            "suggestion": suggestion,
            "lunar": lunar_dict,
        }

    # -------------------------
    # monthly 트리거
    # -------------------------
    if has_monthly_trigger:
        bucket = _bucket_month_day(today)
        _, center, window_days, _ = _pick_near_center(
            today,
            prefer_monthly=True,
            prefer_yearly=False,
        )
        why = "이번 달 흐름이 비교적 뚜렷하게 작용합니다."
        suggestion = "속도보다는 방향성을 점검하세요."

        return {
            "when": f"이달 중 ({bucket})",
            "precision": "월간",
            "window": _window_str(center, window_days, calendar="양력"),
            "calendar": "양력",
            "why": why,
            "suggestion": suggestion,
            "lunar": lunar_dict,
        }

    # -------------------------
    # yearly 트리거
    # -------------------------
    if has_yearly_trigger:
        _, center, window_days, _ = _pick_near_center(
            today,
            prefer_monthly=False,
            prefer_yearly=True,
        )
        why = "올해 전체 흐름의 영향을 받는 시기입니다."
        suggestion = "급한 변화보다는 큰 방향을 유지하세요."

        return {
            "when": "올해 중",
            "precision": "연간",
            "window": _window_str(center, window_days, calendar="양력"),
            "calendar": "양력",
            "why": why,
            "suggestion": suggestion,
            "lunar": lunar_dict,
        }

    # -------------------------
    # 기본 fallback
    # -------------------------
    _, center, window_days, _ = _pick_near_center(
        today,
        prefer_monthly=False,
        prefer_yearly=False,
    )

    return {
        "when": "이달 중",
        "precision": "기본",
        "window": _window_str(center, window_days, calendar="양력"),
        "calendar": "양력",
        "why": "특별한 트리거가 감지되지 않아, 중립적인 흐름으로 안내합니다.",
        "suggestion": "큰 결정은 시간을 두고 검토하는 것이 좋습니다.",
        "lunar": lunar_dict,
    }
