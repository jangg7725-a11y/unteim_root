# -*- coding: utf-8 -*-
"""
대운/세운 계산 모듈
- calc_dayun(birth_kst, sex, pillars, count=8)
- calc_seyun(birth_kst, years=12)

규칙(보편식, 본 프로젝트 기준):
1) 대운 방향
   - 연간(Year Stem)의 음양과 성별로 결정
     · 양(甲丙戊庚壬) & 남자 → 순행(forward)
     · 음(乙丁己辛癸) & 여자 → 순행(forward)
     · 그 외 → 역행(backward)
   (※ 분파에 따라 변형이 있으나, 본 프로젝트는 이 규칙을 채택)

2) 대운 시작시점/나이
   - 출생 시각(KST)으로부터 **다음 절기(주절기, JieQi)**까지의 시간 차이를 사용
   - 그 시간차를 그대로 연(yr)/월(mo)/일(day)로 환산해 `start_age_ymd`와
     소수 연(`start_age_years`)을 구함
   - 실제 시작일시는 그 다음 절기의 시각을 그대로 `start_datetime_kst`로 표기
   (※ 학파에 따라 1일=1년/3일=1년 등의 환산식을 쓰기도 하나, 이전 단계 출력과
      일치시키기 위해 "직접 환산" 방식을 사용)

3) 대운 주기
   - 월주(月柱)를 기준으로 10년마다 간지 index를 +1(순행) 또는 -1(역행) 진행
   - `count` 개수만큼 10년 주기를 산출

4) 세운
   - 지정한 연수(years)만큼, 각 연도의 연주(입춘 보정 반영)를 생성
"""

from __future__ import annotations
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .pillars import STEMS, BRANCHES, y_ganzhi_from_year_solar
from .solar_terms import get_principal_terms

KST = ZoneInfo("Asia/Seoul")

# ── 표준 규칙 고정 ─────────────────────────────────────────────────────────
DAYUN_RULE = {
    "term_kind": "principal",   # principal = 주절기(중기 12개), all = 24절기 전체
    "anchor": "next",           # next = 출생 직후 다음 절기, prev = 직전 절기
    "age_mode": "delta_exact",  # delta_exact = 실제 시간차, divide3 = 3일=1년
}

# ──────────────────────────────────────────────────────────────────────────────
# 유틸

YANG_STEMS = set(["甲", "丙", "戊", "庚", "壬"])
YIN_STEMS  = set(["乙", "丁", "己", "辛", "癸"])

def is_yang_stem(stem: str) -> bool:
    return stem in YANG_STEMS

def _sb_to_idx(stem: str, branch: str) -> int:
    """천간/지지를 60갑자 index로 근사 매핑 (0~59)"""
    for i in range(60):
        if STEMS[i % 10] == stem and BRANCHES[i % 12] == branch:
            return i
    return 0

def _idx_step(idx: int, step: int) -> int:
    return (idx + step) % 60

def _to_ymd(delta: timedelta) -> Dict[str, int]:
    """
    시간차를 '대략적' yr/mo/day로 환산 (yr=365일, mo=30일 간주)
    """
    days = int(delta.total_seconds() // 86400)
    years = days // 365
    days -= years * 365
    months = days // 30
    days -= months * 30
    return {"years": years, "months": months, "days": days}

def _to_years_float(delta: timedelta) -> float:
    return round(delta.total_seconds() / (365.2425 * 86400.0), 2)


# ──────────────────────────────────────────────────────────────────────────────
# 절기 보조

def _pick_term(dt_kst: datetime, *, kind: str = "principal", anchor: str = "next") -> datetime:
    """
    dt_kst 기준으로 '다음/이전' 절입 시각을 반환.
    kind="principal" → 12중기(경도 0,30,...,330°)만 사용
    kind="all"       → 24절기 전체 사용
    anchor="next"|"prev"
    """
    if dt_kst.tzinfo is None:
        dt_kst = dt_kst.replace(tzinfo=KST)

    year = dt_kst.year
    terms = []
    for y in (year - 1, year, year + 1):
        for item in get_principal_terms(y):  # 여기 결과에 'deg' 포함되어 있음 (0~345)
            deg = int(item.get("degree") or item.get("deg") or item["degree"])
            # principal만 쓸 때는 30의 배수만 통과
            if kind == "principal" and (deg % 30 != 0):
                continue
            t_utc = datetime.fromisoformat(item["time_utc"].replace("Z", "+00:00"))
            t_kst = t_utc.astimezone(KST)
            terms.append((t_kst, deg))

    terms.sort(key=lambda x: x[0])

    if anchor == "next":
        for t_kst, _ in terms:
            if t_kst > dt_kst:
                return t_kst
        return terms[-1][0]  # 안전장치
    else:  # "prev"
        prev = terms[0][0]
        for t_kst, _ in terms:
            if t_kst >= dt_kst:
                return prev
            prev = t_kst
        return prev



# ──────────────────────────────────────────────────────────────────────────────
# 대운

def _dayun_direction(sex: str, year_stem: str) -> str:
    """
    보편식:
      - (양간 & 남자) or (음간 & 여자) → forward
      - else → backward
    """
    yang = is_yang_stem(year_stem)
    if (yang and sex == "M") or ((not yang) and sex == "F"):
        return "forward"
    return "backward"

def calc_dayun(
    birth_kst: datetime,
    sex: str,
    pillars: Dict[str, Dict[str, str]],
    count: int = 8,
) -> Dict[str, object]:
    """
    반환 예시:
    {
      "direction": "backward",
      "start_age_years": 0.14,
      "start_age_ymd": {"years":0, "months":1, "days":20},
      "start_datetime_kst": "1966-12-24 10:30",
      "cycles": [
        {"order":1, "start_age":10, "pillar":{"stem":"庚","branch":"子"}},
        ...
      ],
      "cycle_starts": [{"order":1, "start_date_kst":"1976-12-24"}, ...]
    }
    """
    # 보정
    if birth_kst.tzinfo is None:
        birth_kst = birth_kst.replace(tzinfo=KST)

    year_stem = pillars["year"]["stem"]
    direction = _dayun_direction(sex, year_stem)
    step = 1 if direction == "forward" else -1

    # 다음 '주절기'까지의 시간차 → 시작나이/시작일시
    next_term = _pick_term(
        birth_kst,
        kind=DAYUN_RULE["term_kind"],
        anchor=DAYUN_RULE["anchor"],
    )

    delta = next_term - birth_kst
    start_age_ymd = _to_ymd(delta)
    start_age_years = _to_years_float(delta)
    start_datetime_kst = next_term.strftime("%Y-%m-%d %H:%M")

    # 월주에서 시작하여 10년마다 +1/-1씩 (count 회)
    m_idx = _sb_to_idx(pillars["month"]["stem"], pillars["month"]["branch"])
    cycles: List[Dict[str, object]] = []
    cycle_starts: List[Dict[str, object]] = []

    # 대운 1회차의 '연 나이'는 보통 10세로 간주(전통식 표기)
    for i in range(1, count + 1):
        idx = _idx_step(m_idx, step * i)
        stem, branch = STEMS[idx % 10], BRANCHES[idx % 12]
        cycles.append({
            "order": i,
            "start_age": i * 10,
            "pillar": {"stem": stem, "branch": branch},
        })
        # 실제 시작 '날짜'는 첫 대운 시작일에서 10년*i 만큼 더한 날
        cycle_start_dt = next_term.replace(year=next_term.year + 10 * (i - 1))
        cycle_starts.append({
            "order": i,
            "start_date_kst": cycle_start_dt.strftime("%Y-%m-%d"),
        })

    return {
        "direction": direction,
        "start_age_years": start_age_years,
        "start_age_ymd": start_age_ymd,
        "start_datetime_kst": start_datetime_kst,
        "cycles": cycles,
        "cycle_starts": cycle_starts,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 세운

def calc_seyun(birth_kst: datetime, years: int = 12) -> List[Dict[str, object]]:
    """
    출생 연도부터 years개 연도에 대한 '연주(세운)' 리스트
    """
    if birth_kst.tzinfo is None:
        birth_kst = birth_kst.replace(tzinfo=KST)

    out: List[Dict[str, object]] = []
    start_year = birth_kst.year
    for y in range(start_year, start_year + years):
        yp = y_ganzhi_from_year_solar(datetime(y, 6, 1, tzinfo=KST))
        out.append({"year": y, "stem": yp.stem, "branch": yp.branch})
    return out
# 호환용 (이전 함수명 지원)
def _next_principal_term_after(dt_kst):
    return _pick_term(dt_kst, kind=DAYUN_RULE["term_kind"], anchor="next")

