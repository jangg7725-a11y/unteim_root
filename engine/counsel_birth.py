# -*- coding: utf-8 -*-
"""
상담용 생년월일 문자열 정규화 — 엔진은 KST 기준 'YYYY-MM-DD HH:MM'.

- 양력(solar): 입력 날짜·시각 그대로.
- 음력(lunar / lunar_leap): korean-lunar-calendar로 양력 날짜로 바꾼 뒤, 시·분은 그대로 붙인다.
  사주·절기·대운은 이 변환된 양력 시각만 사용한다.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


def normalize_birth_string(
    date_str: str,
    time_str: str,
    calendar_api: str,
) -> str:
    """
    - solar: date_str(YYYY-MM-DD) + time_str(HH:MM) → 그대로 합침
    - lunar / lunar_leap: korean-lunar-calendar로 양력일로 변환 후 같은 시각 부착
    """
    d = (date_str or "").strip()
    t = (time_str or "").strip() or "12:00"
    if len(t) == 5 and t[2] == ":":
        pass
    else:
        raise ValueError("time은 HH:MM 형식이어야 합니다.")

    cal = (calendar_api or "solar").strip().lower()
    if cal not in ("solar", "lunar", "lunar_leap"):
        cal = "solar"

    if cal == "solar":
        return _validate_and_join(d, t)

    from korean_lunar_calendar import KoreanLunarCalendar

    parts = d.split("-")
    if len(parts) != 3:
        raise ValueError("date는 YYYY-MM-DD 형식이어야 합니다.")
    y, mo, day = int(parts[0]), int(parts[1]), int(parts[2])
    is_leap = cal == "lunar_leap"
    kcal = KoreanLunarCalendar()
    if not kcal.setLunarDate(y, mo, day, is_leap):
        raise ValueError("유효하지 않은 음력 날짜이거나 변환할 수 없습니다.")

    solar_iso = kcal.SolarIsoFormat()
    s = (solar_iso or "").strip().split()[0]
    if len(s) < 10:
        raise ValueError("음력→양력 변환 결과를 읽을 수 없습니다.")
    return _validate_and_join(s[:10], t)


def _validate_and_join(date_part: str, time_part: str) -> str:
    from datetime import datetime

    s = f"{date_part} {time_part}"
    try:
        datetime.strptime(s, "%Y-%m-%d %H:%M")
    except Exception as e:
        raise ValueError("생년월일·시간 형식이 올바르지 않습니다.") from e
    return s


def map_gender_to_label(gender: str) -> str:
    g = (gender or "").strip().lower()
    if g in ("male", "m", "남", "남자"):
        return "남성"
    if g in ("female", "f", "여", "여자"):
        return "여성"
    return gender or "미입력"


def birth_request_to_profile(req: Dict[str, Any]) -> Dict[str, Any]:
    """API/프론트 공통 dict에서 상담 프로필 메타."""
    return {
        "name": (req.get("name") or "").strip() or "익명",
        "gender_label": map_gender_to_label(str(req.get("gender") or "")),
        "calendar_api": (req.get("calendarApi") or req.get("calendar") or "solar"),
        "birth_date": (req.get("date") or req.get("birthDate") or "").strip(),
        "birth_time": (req.get("time") or req.get("birthTime") or "").strip(),
    }
