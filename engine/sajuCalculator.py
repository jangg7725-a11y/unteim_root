# unteim/engine/sajuCalculator.py
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple
from datetime import datetime
from zoneinfo import ZoneInfo

# -----------------------------
# 기본 상수 / 인덱스
# -----------------------------
KST = ZoneInfo("Asia/Seoul")

HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

GAN_TO_IDX = {g: i for i, g in enumerate(HEAVENLY_STEMS)}
JI_TO_IDX = {j: i for i, j in enumerate(EARTHLY_BRANCHES)}

# -----------------------------
# 내부 모듈 (프로젝트 내부)
# -----------------------------
from .types import GanJi, SajuPillars  # GanJi: gan/ji, SajuPillars: gan/ji 리스트 구조
from .saju_core_pillars import year_ganji, day_ganji, hour_ganji  # (dt)->GanJi / (dt)->GanJi / (dt, day_idx)->GanJi

from .month_stem_resolver import BRANCH_HANJA_TO_KOR, MonthStemResolver
from .month_branch_resolver import resolve_month_branch

_KOR_JI_TO_HANJA = {v: k for k, v in BRANCH_HANJA_TO_KOR.items()}

from .ohengAnalyzer import analyze_oheng
from .shinsalDetector import detect_shinsal

from .wolwoon_engine import WolWoonEngine
from .sewun_engine import SewoonEngine
from .daewoon_engine import DaewoonEngine

# ✅ seg_start 없이 안정적으로 월절기 계산하는 astro_solar_terms 기반
from .astro_solar_terms import compute_solar_terms_for_year

# -----------------------------
# 유틸
# -----------------------------
def _parse_birth_kst(birth_str: str) -> datetime:
    """
    birth_str: "YYYY-MM-DD HH:MM" (KST 가정)
    """
    dt = datetime.strptime(birth_str.strip(), "%Y-%m-%d %H:%M")
    return dt.replace(tzinfo=KST)


def _ensure_kst(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=KST)
    return dt.astimezone(KST)


def _gan_idx(gan: str) -> int:
    if gan not in GAN_TO_IDX:
        raise ValueError(f"Invalid heavenly stem: {gan}")
    return GAN_TO_IDX[gan]


def _to_shinsal_pillars(pillars: SajuPillars) -> Dict[str, Tuple[str, str]]:
    """
    detect_shinsal()가 기대하는 구조로 변환:
    {
        "year": ("간", "지"),
        "month": ("간", "지"),
        "day": ("간", "지"),
        "hour": ("간", "지"),
    }
    """
    gan_list = list(getattr(pillars, "gan", []) or [])
    ji_list = list(getattr(pillars, "ji", []) or [])

    if len(gan_list) != 4 or len(ji_list) != 4:
        raise ValueError("SajuPillars는 gan/ji 각각 4개 값이 있어야 합니다.")

    return {
        "year": (str(gan_list[0]), str(ji_list[0])),
        "month": (str(gan_list[1]), str(ji_list[1])),
        "day": (str(gan_list[2]), str(ji_list[2])),
        "hour": (str(gan_list[3]), str(ji_list[3])),
    }



def _safe_run(name: str, fn, default):
    try:
        return fn()
    except Exception as e:
        return {"error": f"{name}: {type(e).__name__}: {e}", "data": default}


# -----------------------------
# ✅ 월지/월절기 안정판 (NO seg_start)
# -----------------------------
class _SolarTermLoaderBridge:
    """
    month_branch_resolver.resolve_month_branch()가 기대하는
    find_adjacent_principal_term_name(dt) → 직전 절기명.
    astro_solar_terms(황경 버킷) + 연초 경계를 위해 year±1 절기 시각을 합쳐 직전 절입을 찾음.
    """

    def find_adjacent_principal_term_name(self, dt_kst: datetime) -> str:
        candidates = []
        for yy in (dt_kst.year - 1, dt_kst.year, dt_kst.year + 1):
            candidates.extend(compute_solar_terms_for_year(yy))
        candidates.sort(key=lambda t: t.dt_kst)
        last = None
        for t in candidates:
            if t.dt_kst <= dt_kst:
                last = t
            else:
                break
        if last is None:
            return "입춘"
        name = getattr(last, "name", None)
        return name if isinstance(name, str) and name else "입춘"


_SOLAR_TERM_BRIDGE = _SolarTermLoaderBridge()


def _month_branch_hanja_from_resolver(dt_kst: datetime) -> str:
    kor = resolve_month_branch(_SOLAR_TERM_BRIDGE, dt_kst)
    return _KOR_JI_TO_HANJA.get(kor, kor)


def _month_term_meta_stable(dt_kst: datetime) -> Tuple[Optional[str], Optional[str]]:
    """
    (month_term_name, month_term_time_kst_iso)
    - year±1 절기 시각을 합쳐 dt 직전 절기(prev)를 구해 month_term로 사용
    """
    candidates = []
    for yy in (dt_kst.year - 1, dt_kst.year, dt_kst.year + 1):
        candidates.extend(compute_solar_terms_for_year(yy))
    candidates.sort(key=lambda t: t.dt_kst)
    prev_t = None
    for t in candidates:
        if t.dt_kst <= dt_kst:
            prev_t = t
        else:
            break
    if prev_t is None:
        return None, None

    name = getattr(prev_t, "name", None)
    dt_prev = getattr(prev_t, "dt_kst", None)

    if isinstance(dt_prev, datetime):
        return name, dt_prev.isoformat()
    return name, None


# -----------------------------
# ✅ 외부 API (핵심)
# -----------------------------
def calculate_saju(birth_str: str) -> SajuPillars:
    """
    반환: SajuPillars(gan[4], ji[4], meta 가능)
    - year/month/day/hour GanJi 계산
    - month는 seg_start 없이 절기 기반 안정판 사용
    - meta에 month_term, month_term_time_kst 저장
    """
    dt_kst = _ensure_kst(_parse_birth_kst(birth_str))

    # 1) 년주
    y: GanJi = year_ganji(dt_kst)
    year_stem_char = y.gan if isinstance(y.gan, str) else HEAVENLY_STEMS[int(y.gan)]

    # 2) 월주 (안정판: seg_start 제거, idx 안정화)
    ms = MonthStemResolver()

    month_branch_hanja = _month_branch_hanja_from_resolver(dt_kst)

    month_stem = ms.resolve(year_stem_char, month_branch_hanja)   # year_stem_char = 연간(갑을병정..)
    m = GanJi(gan=month_stem, ji=month_branch_hanja)

    # 월절기 메타 (이름 + 시간) — pillars.meta에 한 번만 기록
    month_term, month_term_time_kst = _month_term_meta_stable(dt_kst)

    # 3) 일주
    d: GanJi = day_ganji(dt_kst)
    day_stem_idx = _gan_idx(d.gan if isinstance(d.gan, str) else HEAVENLY_STEMS[int(d.gan)])

    # 4) 시주
    h: GanJi = hour_ganji(dt_kst, day_stem_idx)

    def _as_gan(g):
        return HEAVENLY_STEMS[g] if isinstance(g, int) else g

    def _as_ji(j):
        return EARTHLY_BRANCHES[j] if isinstance(j, int) else j

    pillars = SajuPillars(
        gan=[_as_gan(y.gan), _as_gan(m.gan), _as_gan(d.gan), _as_gan(h.gan)],
        ji=[_as_ji(y.ji), _as_ji(m.ji), _as_ji(d.ji), _as_ji(h.ji)],
    )

    pillars.meta["month_term"] = month_term
    pillars.meta["month_term_time_kst"] = month_term_time_kst

    return pillars


def analyze_saju(dt_or_birth: Any) -> Dict[str, Any]:
    """
    간단 분석(오행/신살/3대운)까지 한 번에 묶어 반환.
    - dt(datetime) 또는 birth_str("YYYY-MM-DD HH:MM") 둘 다 지원
    """
    if isinstance(dt_or_birth, datetime):
        dt_kst = _ensure_kst(dt_or_birth)
        birth_str = dt_kst.strftime("%Y-%m-%d %H:%M")
    else:
        birth_str = str(dt_or_birth)
        dt_kst = _ensure_kst(_parse_birth_kst(birth_str))

    pillars = calculate_saju(birth_str)

    oheng = _safe_run("oheng", lambda: analyze_oheng(pillars), default={})
    shinsal = _safe_run("shinsal", lambda: detect_shinsal(_to_shinsal_pillars(pillars)), default={})

    wolwoon = _safe_run(
        "wolwoon",
        lambda: WolWoonEngine().to_public(WolWoonEngine().build_year_segments(dt_kst.year)),
        default=[],
    )
    sewun = _safe_run(
        "sewun",
        lambda: SewoonEngine().to_public(SewoonEngine().build(dt_kst, dt_kst.year, dt_kst.year + 5)),
        default=[],
    )
    daewoon = _safe_run(
        "daewoon",
        lambda: DaewoonEngine().to_public(DaewoonEngine().build(dt_kst, gender="F", count=10)),
        default=[],
    )

    out = {
        "birth_str": birth_str,
        "pillars": {
            "gan": pillars.gan,
            "ji": pillars.ji,
            "meta": getattr(pillars, "meta", {}),
        },
        "oheng": oheng,
        "shinsal": shinsal,
        "wolwoon": wolwoon,
        "sewun": sewun,
        "daewoon": daewoon,
    }
    return out
