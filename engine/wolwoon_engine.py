# unteim/engine/wolwoon_engine.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from zoneinfo import ZoneInfo

from .solar_terms_loader import SolarTermsLoader
from .month_branch_resolver import MonthBranchResolver
from .month_stem_resolver import MonthStemResolver
from .wolwoon_scoring import score_pattern
from .wolwoon_top3 import pick_top3

def _normalize_month_branch(mb):
    """
    mb가 '午' / '오' / '지지: 午' / dict/None 등 어떤 형태로 와도
    월지(한글: 자~해) 또는 월지(한자: 子~亥) 중 하나로 뽑아줌.
    실패하면 None.
    """
    if mb is None:
        return None

    # dict로 잘못 넘어오는 케이스 방어
    if isinstance(mb, dict):
        # 흔한 키 후보들
        for k in ("month", "월", "month_branch", "branch", "ji", "지"):
            if k in mb:
                mb = mb[k]
                break

    s = str(mb).strip()
    if not s:
        return None

    # 1) 한자 지지(子..亥) 직접 포함 탐색
    hanja_branches = "子丑寅卯辰巳午未申酉戌亥"
    for ch in s:
        if ch in hanja_branches:
            return ch  # 한자 지지로 반환

    # 2) 한글 지지(자..해) 직접 포함 탐색
    kor_branches = ["자","축","인","묘","진","사","오","미","신","유","술","해"]
    for b in kor_branches:
        if b in s:
            return b  # 한글 지지로 반환

    return None

def build_features_by_pattern(
    pattern_signals,
    month_branch=None,
    natal_branches=None,
    unseong_stage=None,
    oheng_summary=None,
    is_gongmang=False,
):
    """
    최종판 안정화용:
    - 패턴 스코어링에서 필요한 'features_by_pattern' dict를 항상 반환
    - 내부 스펙이 바뀌어도 엔진이 멈추지 않도록 방어

    return:
      dict[pattern_id] = {
        "signals": <원본 시그널>,
        "month_branch": ...,
        "natal_branches": ...,
        "unseong_stage": ...,
        "oheng_summary": ...,
        "is_gongmang": ...,
      }
    """
    out = {}

    if not pattern_signals:
        return out

    # pattern_signals 가 dict {pid: signals} 형태면 그대로 사용
    if isinstance(pattern_signals, dict):
        for pid, sig in pattern_signals.items():
            out[pid] = {
                "signals": sig,
                "month_branch": month_branch,
                "natal_branches": natal_branches,
                "unseong_stage": unseong_stage,
                "oheng_summary": oheng_summary,
                "is_gongmang": is_gongmang,
            }
        return out

    # list/tuple 형태면 pid를 생성해서 담기
    if isinstance(pattern_signals, (list, tuple)):
        for i, sig in enumerate(pattern_signals, start=1):
            pid = getattr(sig, "id", None) or f"p{i:02d}"
            out[pid] = {
                "signals": sig,
                "month_branch": month_branch,
                "natal_branches": natal_branches,
                "unseong_stage": unseong_stage,
                "oheng_summary": oheng_summary,
                "is_gongmang": is_gongmang,
            }
        return out

    # 그 외 타입이면 안전하게 빈 dict
    return out

KST = ZoneInfo("Asia/Seoul")

# 인월(寅)부터 축월까지 — MonthStemResolver가 한글 지지를 받음
_BRANCHES_FROM_IN: List[str] = ["인", "묘", "진", "사", "오", "미", "신", "유", "술", "해", "자", "축"]


def _inc_month(y: int, m: int, step: int = 1) -> tuple[int, int]:
    """(y, m)을 step개월만큼 이동."""
    total = (y * 12 + (m - 1)) + step
    ny = total // 12
    nm = (total % 12) + 1
    return ny, nm


@dataclass(frozen=True)
class MonthSegment:
    start_datetime: datetime
    end_datetime: datetime
    term_name: str           # 예: "입춘", "경칩"...
    month_branch: str        # 예: "寅", "卯"...
    month_stem: str          # 예: "甲", "乙"...
    month_pillar: str        # 예: "甲寅"


class WolWoonEngine:
    """
    월운 엔진:
    - 특정 연도에 대해 12절기 구간(입춘~다음해 입춘)을 만들고
    - 각 구간의 월지/월간/월주를 계산한다.
    """

    def __init__(self, loader: Optional[SolarTermsLoader] = None):
        self.loader = loader or SolarTermsLoader()
        self.branch_resolver = MonthBranchResolver(self.loader)
        self.stem_resolver = MonthStemResolver()

    def _load_terms_dt(self, year: int) -> Dict[str, datetime]:
        """
        SolarTermsLoader가 datetime 또는 ISO 문자열을 반환할 수 있으므로
        둘 다 안전하게 처리해서 KST timezone-aware datetime으로 통일한다.
        """
        raw = self.loader.get_year_terms(year)  # {name: datetime|str}
        out: Dict[str, datetime] = {}

        for name, dt in raw.items():
            if dt is None:
                continue

            # 1) 문자열이면 ISO 파싱
            if isinstance(dt, str):
                try:
                    dt = datetime.fromisoformat(dt)
                except Exception:
                    # ISO 포맷이 아닐 수도 있으니, 마지막 방어
                    continue

            # 2) naive datetime이면 KST 부여
            if isinstance(dt, datetime):
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=KST)
                else:
                    dt = dt.astimezone(KST)

                out[name] = dt

        return out


    def build_year_segments(self, year: int) -> List[MonthSegment]:
        """
        year년 입춘 시각부터 (year+1)년 입춘 직전까지, 인접 절입 시각마다 한 구간씩 만든다.
        (캐시에 있는 절기 수에 따라 구간 개수는 달라질 수 있음. 월지는 인월부터 12지를 순환.)
        """
        terms_this = self._load_terms_dt(year)
        terms_next = self._load_terms_dt(year + 1)

        if "입춘" not in terms_this or "입춘" not in terms_next:
            raise RuntimeError(f"[WolWoon] 입춘이 캐시에 없습니다. year={year}")

        start_ipchun = terms_this["입춘"]
        end_ipchun_next = terms_next["입춘"]

        # 기준 시각 리스트(절기) 만들기: year의 12절기(입춘 포함)만 뽑고 정렬
        # month_branch_resolver 쪽이 내부적으로 “입춘 기준” 매핑을 하므로,
        # 여기서는 start/end 경계만 정확하면 된다.
        cut_points = sorted([dt for dt in terms_this.values() if start_ipchun <= dt < end_ipchun_next])
        if not cut_points:
            raise RuntimeError(f"[WolWoon] 입춘~다음해 입춘 사이 절기 시각이 없습니다. year={year}")
        # 안전: 시작점이 입춘으로 시작되도록 보정
        if cut_points[0] != start_ipchun:
            cut_points = [start_ipchun] + [dt for dt in cut_points if dt != start_ipchun]

        # 끝점은 다음해 입춘
        cut_points.append(end_ipchun_next)

        segments: List[MonthSegment] = []
        for i in range(len(cut_points) - 1):
            seg_start = cut_points[i]
            seg_end = cut_points[i + 1]

            term_name: Optional[str] = None
            if hasattr(self.loader, "find_adjacent_principal_term_name"):
                term_name = self.loader.find_adjacent_principal_term_name(seg_start)
            if not term_name:
                term_name = "절기"

            m_branch = _BRANCHES_FROM_IN[i % 12]
            m_stem = self.stem_resolver.resolve(year, m_branch)
            month_branch = m_branch
            month_stem = m_stem
            month_pillar = f"{month_stem}{month_branch}"

            segments.append(
                MonthSegment(
                    start_datetime=seg_start,
                    end_datetime=seg_end,
                    term_name=term_name,
                    month_branch=month_branch,
                    month_stem=month_stem,
                    month_pillar=month_pillar,
                )
            )

        return segments

    def to_public(self, segments: List[MonthSegment]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for s in segments:
            out.append(
                {
                    "start": s.start_datetime.isoformat(),
                    "end": s.end_datetime.isoformat(),
                    "term": s.term_name,
                    "month_branch": s.month_branch,
                    "month_stem": s.month_stem,
                    "month_pillar": s.month_pillar,
                }
            )
        return out
    

    # 아래는 full_analyzer가 찾는 '후보 메서드명'들을 전부 build_months로 연결
    def calculate(self, year: int | None = None, num_months: int = 12, months: int | None = None, **kwargs) -> List[Dict[str, Any]]:
        return self.build_months(year=year, num_months=int(months if months is not None else num_months), **kwargs)

    def build(self, year: int | None = None, num_months: int = 12, months: int | None = None, **kwargs) -> List[Dict[str, Any]]:
        return self.build_months(year=year, num_months=int(months if months is not None else num_months), **kwargs)

    def run(self, year: int | None = None, num_months: int = 12, months: int | None = None, **kwargs) -> List[Dict[str, Any]]:
        return self.build_months(year=year, num_months=int(months if months is not None else num_months), **kwargs)

    def make(self, year: int | None = None, num_months: int = 12, months: int | None = None, **kwargs) -> List[Dict[str, Any]]:
        return self.build_months(year=year, num_months=int(months if months is not None else num_months), **kwargs)

    def generate(self, year: int | None = None, num_months: int = 12, months: int | None = None, **kwargs) -> List[Dict[str, Any]]:
        return self.build_months(year=year, num_months=int(months if months is not None else num_months), **kwargs)

    def create(self, year: int | None = None, num_months: int = 12, months: int | None = None, **kwargs) -> List[Dict[str, Any]]:
        return self.build_months(year=year, num_months=int(months if months is not None else num_months), **kwargs)

    def get_months(self, year: int | None = None, num_months: int = 12, months: int | None = None, **kwargs) -> List[Dict[str, Any]]:
        return self.build_months(year=year, num_months=int(months if months is not None else num_months), **kwargs)

    def timeline(self, year: int | None = None, num_months: int = 12, months: int | None = None, **kwargs) -> List[Dict[str, Any]]:
        return self.build_months(year=year, num_months=int(months if months is not None else num_months), **kwargs)

    def get_list(self, year: int | None = None, num_months: int = 12, months: int | None = None, **kwargs) -> List[Dict[str, Any]]:
        return self.build_months(year=year, num_months=int(months if months is not None else num_months), **kwargs)

    def get_items(self, year: int | None = None, num_months: int = 12, months: int | None = None, **kwargs) -> List[Dict[str, Any]]:
        return self.build_months(year=year, num_months=int(months if months is not None else num_months), **kwargs)

    def to_list(self, year: int | None = None, num_months: int = 12, months: int | None = None, **kwargs) -> List[Dict[str, Any]]:
        return self.build_months(year=year, num_months=int(months if months is not None else num_months), **kwargs)

    def build_months(
        self,
        year: int | None = None,
        months: int = 12,
        num_months: int | None = None,
        **kwargs,
    ) -> list[dict]:
        """
        ✅ 최종 안전 버전(클래스 메서드):
        - full_analyzer가 어떤 이름으로 호출해도 동작하도록 months/num_months 모두 지원
        - label = YYYY-MM
        - month_branch/month_stem/month_pillar 생성
        - (조건 충족 시) wolwoon_top3 계산
        """

        total = int(num_months) if num_months is not None else int(months)

        # start_year/start_month 우선 (Engine 생성 시 세팅되는 값)
        start_year = getattr(self, "start_year", None) or getattr(self, "year", None) or year
        start_month = getattr(self, "start_month", None) or getattr(self, "month", None)

        if start_year is None:
            start_year = year if year is not None else 1990
        if start_month is None:
            start_month = 1

        y, m = int(start_year), int(start_month)

        # TOP3 입력(없으면 컨테이너)
        pattern_signals = getattr(self, "pattern_signals", None) or {}
        natal_branches = getattr(self, "natal_branches", None) or []
        unseong_stage = getattr(self, "unseong_stage", None)
        oheng_summary = getattr(self, "oheng_summary", None)
        is_gongmang = bool(getattr(self, "is_gongmang", False))

        # 그레고리 월 → 지지(월지) 매핑(안전 기본)
        greg_month_to_branch = {
            1: "축",  2: "인",  3: "묘",  4: "진",
            5: "사",  6: "오",  7: "미",  8: "신",
            9: "유", 10: "술", 11: "해", 12: "자",
        }

        items: list[dict] = []

        for i in range(total):
            label = f"{y:04d}-{m:02d}"

            month_branch = greg_month_to_branch.get(m, "")
            month_stem = ""
            try:
                if month_branch:
                    month_stem = self.stem_resolver.resolve(y, month_branch)
            except Exception:
                month_stem = ""

            month_pillar = f"{month_stem}{month_branch}" if (month_stem and month_branch) else ""

            # start/end (월 경계) — 없더라도 키는 유지
            try:
                start_dt = datetime(y, m, 1, tzinfo=KST)
                ny, nm = _inc_month(y, m, 1)
                end_dt = datetime(ny, nm, 1, tzinfo=KST)
                start_iso = start_dt.isoformat()
                end_iso = end_dt.isoformat()
            except Exception:
                start_iso = None
                end_iso = None

            item = {
                "kind": "wolwoon",
                "index": i,
                "year": y,
                "month": m,
                "label": label,
                "calendar": "양력",
                "start": start_iso,
                "end": end_iso,
                "term": None,
                "month_branch": month_branch,
                "month_stem": month_stem,
                "month_pillar": month_pillar,
            }

            # TOP3 (조건 충족 시)
            top3_payload: list[dict] = []
            try:
                if month_branch and isinstance(natal_branches, list) and natal_branches:
                    features_by_pattern = build_features_by_pattern(
                        pattern_signals=pattern_signals,
                        month_branch=month_branch,
                        natal_branches=natal_branches,
                        unseong_stage=unseong_stage,
                        oheng_summary=oheng_summary,
                        is_gongmang=is_gongmang,
                    )
                    scored_patterns = [
                        score_pattern(pid, features_by_pattern[pid])
                        for pid in features_by_pattern
                    ]
                    top3_patterns = pick_top3(scored_patterns)

                    top3_payload = [
                        {"id": p.id, "score": p.final_score, "breakdown": p.breakdown}
                        for p in top3_patterns
                    ]
            except Exception:
                top3_payload = []

            item["wolwoon_top3"] = top3_payload
            items.append(item)

            y, m = _inc_month(y, m, 1)

        return items
