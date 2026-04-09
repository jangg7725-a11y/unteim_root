# unteim/engine/daewoon_engine.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Literal, Optional, Tuple
from zoneinfo import ZoneInfo

from .solar_terms_loader import SolarTermsLoader
from .kasi_client import (
    MONTH_BOUNDARY_TERMS,
    get_next_month_boundary_after,
    get_prev_month_boundary_on_or_before,
)
from .month_branch_resolver import TERM_TO_BRANCH
from .month_stem_resolver import MonthStemResolver
from .saju_pillar_adapter import get_year_pillar  # GanJi(gan='甲' or int, ji='子' or int)
from .wolwoon_engine import _normalize_month_branch

KST = ZoneInfo("Asia/Seoul")
Direction = Literal["forward", "backward"]

# ------------------------------------------------------------
# constants & normalization
# ------------------------------------------------------------

HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
MONTH_BRANCH_ORDER = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]

_STEM_KO_TO_HAN = {
    "갑": "甲", "을": "乙", "병": "丙", "정": "丁", "무": "戊",
    "기": "己", "경": "庚", "신": "辛", "임": "壬", "계": "癸",
}
_ELEM_TO_STEM_HAN = {"목": "甲", "화": "丙", "토": "戊", "금": "庚", "수": "壬",
                     "木": "甲", "火": "丙", "土": "戊", "金": "庚", "水": "壬"}

_BRANCH_KO_TO_HAN = {
    "자": "子", "축": "丑", "인": "寅", "묘": "卯", "진": "辰", "사": "巳",
    "오": "午", "미": "未", "신": "申", "유": "酉", "술": "戌", "해": "亥",
}

def _ensure_kst(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=KST)
    return dt.astimezone(KST)

def _normalize_stem(v: Any) -> str:
    """
    입력이 '甲'/'갑'/'목'/'木'/0..9 등으로 와도 최종 '甲..癸' 로 맞춤.
    """
    if isinstance(v, int):
        return HEAVENLY_STEMS[v % 10]
    s = str(v).strip()
    if not s:
        return ""
    # 오행/원소 → 천간(한자)
    s = _ELEM_TO_STEM_HAN.get(s, s)
    # 한글 천간 → 한자 천간
    s = _STEM_KO_TO_HAN.get(s, s)
    return s

def _normalize_branch(v: Any) -> str:
    """
    입력이 '子'/'자' 등으로 와도 최종 월지 순환용 한자(寅..丑)로 맞춤.
    """
    s = str(v).strip()
    if not s:
        return ""
    # 월운 쪽 normalize 함수가 있으면 우선 사용(한자 통일)
    nb = _normalize_month_branch(s)
    if nb:
        s = nb
    # 한글 지지 → 한자 지지
    s = _BRANCH_KO_TO_HAN.get(s, s)
    return s

def gan_to_idx(gan: Any) -> int:
    stem = _normalize_stem(gan)
    if stem not in HEAVENLY_STEMS:
        raise ValueError(f"invalid heavenly stem: {gan!r} -> {stem!r}")
    return HEAVENLY_STEMS.index(stem)

def _branch_next(branch: str, direction: Direction) -> str:
    b = _normalize_branch(branch)
    if b not in MONTH_BRANCH_ORDER:
        raise ValueError(f"invalid month branch: {branch!r} -> {b!r}")
    i = MONTH_BRANCH_ORDER.index(b)
    if direction == "forward":
        return MONTH_BRANCH_ORDER[(i + 1) % 12]
    return MONTH_BRANCH_ORDER[(i - 1) % 12]

# ------------------------------------------------------------
# public models
# ------------------------------------------------------------

@dataclass(frozen=True)
class DaewoonItem:
    start_age: float
    end_age: float
    pillar: str  # 예: "甲寅"

# ------------------------------------------------------------
# engine
# ------------------------------------------------------------

class DaewoonEngine:
    """
    대운 엔진 (안정판)
    - 시작나이: 다음 절기까지 남은 일수 / 3 (전통 관행)
    - 순/역: 연간 음양 + 성별 규칙
    - 10년 단위: 천간/지지 같이 이동
    """

    def __init__(self, loader: Optional[SolarTermsLoader] = None):
        self.loader = loader or SolarTermsLoader()
        self.stem_resolver = MonthStemResolver()

    def _is_yang_year_stem(self, year_stem_char: str) -> bool:
        return year_stem_char in {"甲", "丙", "戊", "庚", "壬"}

    def _direction(self, year_stem_char: str, gender: str) -> Direction:
        is_yang = self._is_yang_year_stem(year_stem_char)
        g = gender.upper()
        if g not in {"M", "F"}:
            raise ValueError("gender must be 'M' or 'F'")
        if g == "M":
            return "forward" if is_yang else "backward"
        return "backward" if is_yang else "forward"

    def _iso_to_kst(self, iso: str) -> datetime:
        t = datetime.fromisoformat(iso)
        if t.tzinfo is None:
            return t.replace(tzinfo=KST)
        return t.astimezone(KST)

    def _month_boundary_events(self, dt_kst: datetime) -> List[Tuple[datetime, str]]:
        """입춘~소한(12절)만 모아 시각순 정렬."""
        if dt_kst.tzinfo is None:
            dt_kst = dt_kst.replace(tzinfo=KST)
        else:
            dt_kst = dt_kst.astimezone(KST)
        y = dt_kst.year
        pairs: List[Tuple[datetime, str]] = []
        for yy in (y - 1, y, y + 1):
            raw = self.loader.get_year_terms(yy)
            for name in MONTH_BOUNDARY_TERMS:
                if name not in raw:
                    continue
                pairs.append((self._iso_to_kst(raw[name]), name))
        pairs.sort(key=lambda x: x[0])
        return pairs

    def _start_age(self, dt_kst: datetime, direction: Direction) -> float:
        """
        순행: 생일~다음 12절까지 일수/3, 역행: 직전 12절~생일 일수/3 (전통 관행).
        """
        if direction == "forward":
            nxt = get_next_month_boundary_after(dt_kst).timestamp_kst
            delta_days = (nxt - dt_kst).total_seconds() / (24 * 3600)
        else:
            prev = get_prev_month_boundary_on_or_before(dt_kst).timestamp_kst
            delta_days = (dt_kst - prev).total_seconds() / (24 * 3600)
        return delta_days / 3.0

    def _first_daewoon_pillar(self, dt_kst: datetime, direction: Direction) -> str:
        last_name: Optional[str] = None
        for _t, name in self._month_boundary_events(dt_kst):
            if _t <= dt_kst:
                last_name = name
            else:
                break
        if last_name is None:
            raise RuntimeError("could not find month boundary on/before birth time")

        month_branch_raw = TERM_TO_BRANCH.get(last_name)
        if not month_branch_raw:
            raise RuntimeError(f"TERM_TO_BRANCH mapping missing for term '{last_name}'")

        month_branch = _normalize_branch(month_branch_raw)
        if month_branch not in MONTH_BRANCH_ORDER:
            raise ValueError(f"invalid month branch from TERM_TO_BRANCH: {month_branch_raw!r} -> {month_branch!r}")

        yg = get_year_pillar(dt_kst)
        year_gan_char = _normalize_stem(yg.gan)
        if not year_gan_char:
            year_gan_char = "甲"  # 최후 안전값
        year_gan_idx = gan_to_idx(year_gan_char)

        # MonthStemResolver가 year_gan_char(천간 한자) + month_branch(지지 한자)로 동작한다고 가정
        month_stem_char = _normalize_stem(self.stem_resolver.resolve(year_gan_char, month_branch))
        if month_stem_char not in HEAVENLY_STEMS:
            raise ValueError(f"invalid month stem from resolver: {month_stem_char!r}")

        next_branch = _branch_next(month_branch, direction)
        step = 1 if direction == "forward" else -1
        next_stem_idx = (gan_to_idx(month_stem_char) + step) % 10
        return f"{HEAVENLY_STEMS[next_stem_idx]}{next_branch}"

    def build(self, dt_kst: datetime, gender: str = "F", count: int = 10) -> List[DaewoonItem]:
        dt_kst = _ensure_kst(dt_kst)

        yg = get_year_pillar(dt_kst)
        year_gan_char = _normalize_stem(yg.gan) or "甲"
        direction = self._direction(year_gan_char, gender)

        start_age = self._start_age(dt_kst, direction)
        pillar = self._first_daewoon_pillar(dt_kst, direction)

        items: List[DaewoonItem] = []
        cur_start = start_age
        cur_pillar = pillar

        step = 1 if direction == "forward" else -1

        for _ in range(count):
            items.append(DaewoonItem(
                start_age=float(cur_start),
                end_age=float(cur_start + 10.0),
                pillar=str(cur_pillar),
            ))

            p = str(cur_pillar).strip()
            p = p[-2:] if len(p) >= 2 else p
            stem = _normalize_stem(p[0])
            branch = _normalize_branch(p[1])

            if stem not in HEAVENLY_STEMS:
                raise ValueError(f"invalid heavenly stem: {p[0]!r} -> {stem!r}")
            if branch not in MONTH_BRANCH_ORDER:
                raise ValueError(f"invalid month branch: {p[1]!r} -> {branch!r}")

            stem_idx = HEAVENLY_STEMS.index(stem)
            branch_idx = MONTH_BRANCH_ORDER.index(branch)

            next_stem = HEAVENLY_STEMS[(stem_idx + step) % 10]
            next_branch = MONTH_BRANCH_ORDER[(branch_idx + step) % 12]
            cur_pillar = f"{next_stem}{next_branch}"
            cur_start += 10.0

        return items

    def to_public(self, items: List[DaewoonItem]) -> List[Dict[str, Any]]:
        return [
            {
                "start_age": round(i.start_age),
                "end_age": round(i.end_age),
                "pillar": i.pillar,
            }
            for i in items
        ]

    def run(
        self,
        pillars: Any = None,
        *,
        birth_str: Optional[str] = None,
        gender: str = "F",
        count: int = 10,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """
        full_analyzer 등에서 birth_str 기준으로 대운 리스트(dict)를 받기 위한 얇은 래퍼.
        """
        del pillars, kwargs
        if not birth_str:
            return []
        s = birth_str.replace("T", " ").strip()
        try:
            dt_kst = datetime.strptime(s[:16], "%Y-%m-%d %H:%M").replace(tzinfo=KST)
        except Exception:
            return []
        items = self.build(dt_kst, gender=gender, count=count)
        return self.to_public(items)
