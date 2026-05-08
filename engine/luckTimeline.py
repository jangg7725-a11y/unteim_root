# -*- coding: utf-8 -*-
"""
engine.luckTimeline

대운(10년) → 세운(연도별) → 월운(절기 경계) → 일운(일별) 타임라인 빌더

- 월운: '입춘~(다음)입춘'을 1년으로 보고, 그 안에서 12개 절기 경계
        [입춘~경칩)=寅, [경칩~청명)=卯, …, [대설~소한)=子, [소한~다음해 입춘)=丑
- 일운: 각 월운의 시작~끝 날짜를 전개하며, 모든 날짜에 일간지(간지)를 부착
- 절기표: kasi_client.get_solar_terms_for_year() 사용
  (현재 평균 절기 폴백. KASI API 연동 시 자동 정밀화)
"""


from __future__ import annotations
from typing import Any, Dict, List, Tuple, TypedDict, Optional, Literal, cast
from datetime import date, datetime, timedelta
import calendar
from .daewoon_calculator import (
    calculate_daewoon,
    HEAVENLY_STEMS,
    EARTHLY_BRANCHES,
    Gender,     # Literal["남", "여"]
    YinYang,    # Literal["양", "음"]
    year_stem_index,
    month_stem_index_from_year_stem,
)
from .daewoon_calculator import BRANCH_INDEX as BR_IDX
from .kasi_client import (
    get_solar_terms_for_year,
    SOLAR_TERM_TO_BRANCH,
    MONTH_BOUNDARY_TERMS,

)
from .saju_utils import summarize_bazi, twelve_stage_of
SewunBoundary = Literal["ipchun", "jan1"]

# -----------------------------
# 유틸: 연/월/일 간지 헬퍼
# -----------------------------
def year_ganji(year: int) -> str:
    stem = HEAVENLY_STEMS[(year - 1984) % 10]
    branch = EARTHLY_BRANCHES[(year - 1984) % 12]
    return stem + branch

def _sexagenary_day_ganji_by_base(d: date) -> str:
    """간편 일간지(기준일 1984-02-02 甲子) — 실서비스 전 교차검증 권장"""
    base = date(1984, 2, 2)
    delta = (d - base).days
    stem = HEAVENLY_STEMS[(delta % 10 + 10) % 10]
    branch = EARTHLY_BRANCHES[(delta % 12 + 12) % 12]
    return stem + branch


# -----------------------------
# 출력 스키마
# -----------------------------
class DayNode(TypedDict, total=False):
    date: str     # 'YYYY-MM-DD'
    ganji: str

class MonthNode(TypedDict, total=False):
    month_idx: int            # 1~12 (입춘년 기준의 1..12)
    ganji: str
    start: str                # 'YYYY-MM-DD'
    end_inclusive: str        # 'YYYY-MM-DD'
    days: List[DayNode]

class YearNode(TypedDict, total=False):
    year: int                 # 라벨 (ipchun: 입춘Y~입춘Y+1)
    ganji: str
    months: List[MonthNode]

class DaewoonNode(TypedDict, total=False):
    age: int
    ganji: str
    years: List[YearNode]


# -----------------------------
# 세운(연운) 범위
# -----------------------------
def calculate_sewun_range(
    start_year: int,
    end_year_inclusive: int,
    *,
    boundary: SewunBoundary = "ipchun",
) -> List[Dict[str, int | str]]:
    out: List[Dict[str, int | str]] = []
    for y in range(int(start_year), int(end_year_inclusive) + 1):
        out.append({"year": int(y), "ganji": year_ganji(y)})
    return out


# -----------------------------
# 월운: 절기 경계 기반 12개 구간 생성
# -----------------------------
def _build_month_windows_for_ipchun_year(label_year: int) -> List[Dict[str, Any]]:
    """
    [입춘(label_year) ~ 입춘(label_year+1)) 구간을 12개 월운으로 분해.
    각 월운: {'idx': 1..12, 'start_dt': datetime, 'end_dt_inclusive': datetime, 'branch_idx': int}
    """
    tbl_this = get_solar_terms_for_year(label_year)
    tbl_next = get_solar_terms_for_year(label_year + 1)

    # [입춘(Y), 경칩(Y), 청명(Y), 입하(Y), 망종(Y), 소서(Y),
    #  입추(Y), 백로(Y), 한로(Y), 입동(Y), 대설(Y), 소한(Y+1), 입춘(Y+1)]
    boundaries: List[datetime] = []
    names_seq = [
        "입춘", "경칩", "청명", "입하", "망종", "소서",
        "입추", "백로", "한로", "입동", "대설",
    ]
    boundaries.append(tbl_this["입춘"])
    for nm in names_seq[1:]:
        boundaries.append(tbl_this[nm])
    boundaries.append(tbl_next["소한"])
    boundaries.append(tbl_next["입춘"])

    months: List[Dict[str, Any]] = []
    for i in range(12):
        start_dt: datetime = boundaries[i]
        end_dt_exclusive: datetime = boundaries[i + 1]
        end_dt_inclusive: datetime = end_dt_exclusive - timedelta(seconds=1)

        boundary_name = MONTH_BOUNDARY_TERMS[i]  # ["입춘","경칩",...,"소한"]
        branch_char = SOLAR_TERM_TO_BRANCH[boundary_name]
        branch_idx = BR_IDX[branch_char]

        months.append({
            "idx": i + 1,
            "start_dt": start_dt,
            "end_dt_inclusive": end_dt_inclusive,
            "branch_idx": branch_idx,
        })
    return months


def _month_ganji_from_year_and_branch(label_year: int, branch_idx: int) -> str:
    """월간지 = 연간에 따른 寅월 시작간 + branch offset 규칙"""
    y_stem_idx = year_stem_index(label_year)
    m_stem_idx = month_stem_index_from_year_stem(y_stem_idx, branch_idx)
    return HEAVENLY_STEMS[m_stem_idx] + EARTHLY_BRANCHES[branch_idx]


# -----------------------------
# 메인: 대운→세운→월운(절기)→일운
# -----------------------------
def build_daewoon_sewun_timeline(
    *,
    birth_year: int,
    gender: Gender,
    yin_yang: YinYang,
    birth_month: int | None = None,
    birth_day: int | None = None,
    birth_hour: int | None = None,
    birth_minute: int | None = None,
    num_cycles: int = 8,
    override_start_age: int | None = None,
    use_month_pillar: bool = True,
    sewun_boundary: SewunBoundary = "ipchun",
    include_months: bool = True,
    include_days: bool = False,
) -> Dict[str, Any]:
    """
    include_months=True & sewun_boundary='ipchun'이면
    월운을 '절기 경계'로 생성, 각 월운에 start/end 날짜를 병기.
    include_days=True면 모든 날짜에 일간지를 항상 부착.
    """

    # 1) 대운 계산
    dlist: List[Dict[str, Any]] = calculate_daewoon(
        birth_year=birth_year,
        gender=gender,
        yin_yang=yin_yang,
        birth_month=birth_month,
        birth_day=birth_day,
        birth_hour=birth_hour,
        birth_minute=birth_minute,
        num_cycles=num_cycles,
        override_start_age=override_start_age,
        use_month_pillar=use_month_pillar,
    )
     
    # 메타 분리
    meta: Dict[str, Any] = {}
    if dlist and isinstance(dlist[-1], dict) and "__meta__" in dlist[-1]:
        meta = cast(Dict[str, Any], dlist[-1]["__meta__"])
        dlist = dlist[:-1]

    # === 자동 계산 주입 (data가 아니라 meta에 기록) ===
    # 1) 출생 4주(간지) 확보: meta.base_pillars 우선 사용
    pillars: Optional[Dict[str, Tuple[str, str]]] = None
    bp = meta.get("base_pillars")
    if isinstance(bp, dict):
        try:
            pillars = {
                "year":  (str(bp["year"][0]),  str(bp["year"][1])),
                "month": (str(bp["month"][0]), str(bp["month"][1])),
                "day":   (str(bp["day"][0]),   str(bp["day"][1])),
                "hour":  (str(bp["hour"][0]),  str(bp["hour"][1])),
            }
        except Exception:
            pillars = None

    # (필요시) 코드 내부의 year_gan/month_br 등으로 보완 가능
    # if pillars is None:
    #     pillars = {
    #         "year":  (year_gan,  year_br),
    #         "month": (month_gan, month_br),
    #         "day":   (day_gan,   day_br),
    #         "hour":  (hour_gan,  hour_br),
    #     }

    if pillars is not None:
        # 2) 오행/십신/용희 요약
        five_bal, ten_bal, useful = summarize_bazi(pillars)
        meta["five_elements_balance"] = five_bal
        meta["ten_gods_balance"] = ten_bal
        meta["useful_elements"] = useful

        # 3) 12운성(월지 기준) — 절입일 보정된 월지 우선
        day_branch: str = pillars["day"][1]
        month_branch_actual = meta.get("month_branch_actual")
        if not isinstance(month_branch_actual, str) or not month_branch_actual:
            month_branch_actual = pillars["month"][1]

        meta["twelve_stage"] = twelve_stage_of(
            month_branch=month_branch_actual,
            day_branch=day_branch,
        )
    else:
        # 4주가 없어도 크래시 방지: 기본값만 채움
        meta.setdefault("five_elements_balance", {})
        meta.setdefault("ten_gods_balance", {})

        mb_guess = meta.get("month_branch_actual")
        db_guess = None

       # day_branch 후보: meta에 미리 채워둔 값이 있으면 사용
       # (없으면 12운성은 생략)
        if "day_branch_actual" in meta and isinstance(meta["day_branch_actual"], str):
            db_guess = meta["day_branch_actual"]

        if isinstance(mb_guess, str) and mb_guess and isinstance(db_guess, str) and db_guess:
            meta["twelve_stage"] = twelve_stage_of(
                month_branch=mb_guess,
                day_branch=db_guess,
            )
       # else: 둘 중 하나라도 없으면 12운성은 생략(에러 방지)


   # 2) 세운 라벨 범위 (근사: 나이 a → 연도 birth_year + a)
    first_age_val = dlist[0].get("age", 0)
    base_start_age: int = int(first_age_val) if isinstance(first_age_val, (int, float)) else int(str(first_age_val))

    out_daewoon: List[DaewoonNode] = []
    for idx, node in enumerate(dlist):
        start_age_i = int(node.get("age", base_start_age + idx * 10))
        end_age_i = start_age_i + 9
        start_year = int(birth_year) + start_age_i
        end_year   = int(birth_year) + end_age_i

        year_nodes: List[YearNode] = []
        for y in range(start_year, end_year + 1):
            y_node: YearNode = {"year": y, "ganji": year_ganji(y)}

            if include_months:
                month_nodes: List[MonthNode] = []

                if sewun_boundary == "ipchun":
                    # 절기 경계 월운
                    windows = _build_month_windows_for_ipchun_year(y)
                    for w in windows:
                        m_idx: int = int(w["idx"])
                        sdt_dt: datetime = cast(datetime, w["start_dt"])
                        edt_dt: datetime = cast(datetime, w["end_dt_inclusive"])
                        sdt: date = sdt_dt.date()
                        edt: date = edt_dt.date()
                        branch_idx: int = int(w["branch_idx"])
                        m_gj = _month_ganji_from_year_and_branch(y, branch_idx)

                        m_node: MonthNode = {
                            "month_idx": m_idx,
                            "ganji": m_gj,
                            "start": sdt.isoformat(),
                            "end_inclusive": edt.isoformat(),
                        }

                        if include_days:
                            day_nodes: List[DayNode] = []
                            cur: date = sdt
                            end_date: date = edt
                            while cur <= end_date:
                                dn: DayNode = {"date": cur.isoformat()}
                                # ✅ 항상 일간지 부착
                                dn["ganji"] = _sexagenary_day_ganji_by_base(cur)
                                day_nodes.append(dn)
                                cur = cur + timedelta(days=1)
                            m_node["days"] = day_nodes

                        month_nodes.append(m_node)

                else:
                    # 달력 기준(jan1)
                    for m in range(1, 13):
                        days_in_month = calendar.monthrange(y, m)[1]
                        sdt: date = date(y, m, 1)
                        edt: date = date(y, m, days_in_month)
                        m_node: MonthNode = {
                            "month_idx": m,
                            "ganji": "",
                            "start": sdt.isoformat(),
                            "end_inclusive": edt.isoformat(),
                        }
                        if include_days:
                            day_nodes: List[DayNode] = []
                            cur: date = sdt
                            end_date: date = edt
                            while cur <= end_date:
                                dn: DayNode = {"date": cur.isoformat()}
                                # ✅ 항상 일간지 부착
                                dn["ganji"] = _sexagenary_day_ganji_by_base(cur)
                                day_nodes.append(dn)
                                cur = cur + timedelta(days=1)
                            m_node["days"] = day_nodes
                        month_nodes.append(m_node)

                y_node["months"] = month_nodes

            year_nodes.append(y_node)

        out_daewoon.append(DaewoonNode(age=start_age_i, ganji=str(node.get("ganji", "")), years=year_nodes))

    # 메타 보강
    meta = {
        **meta,
        "sewun_boundary": sewun_boundary,
        "sewun_label_note": (
            "year=Y means [Ipchun(Y)~Ipchun(Y+1)]" if sewun_boundary == "ipchun"
            else "year=Y means [Jan1(Y)~Dec31(Y)]"
        ),
        "month_mode": ("solar_terms" if (include_months and sewun_boundary == "ipchun") else "gregorian"),
        # ✅ 항상 일간지 계산했다고 명시
        "day_ganji_mode": ("approx_base_1984-02-02" if include_days else "none"),
    }

    return {"birth_year": int(birth_year), "daewoon": out_daewoon, "__meta__": meta}
    