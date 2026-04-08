# unteim/engine/month_branch_resolver.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional

KST = ZoneInfo("Asia/Seoul")


@dataclass
class MonthBranchResolver:
    """
    절기명(입춘~대한)을 받아서 월지(인~축)를 반환.
    - loader가 find_adjacent_principal_term_name(dt_kst)를 지원하면 그걸 우선 사용
    - 없으면 dt.month 기반 안전 fallback 사용
    """

    loader: Optional[object] = None

    # 절기명 -> 월지(지지) 매핑 (입춘~대한, 24절기 기준)
    TERM_TO_BRANCH = {
        # 인월
        "입춘": "인",
        "우수": "인",
        # 묘월
        "경칩": "묘",
        "춘분": "묘",
        # 진월
        "청명": "진",
        "곡우": "진",
        # 사월
        "입하": "사",
        "소만": "사",
        # 오월
        "망종": "오",
        "하지": "오",
        # 미월
        "소서": "미",
        "대서": "미",
        # 신월
        "입추": "신",
        "처서": "신",
        # 유월
        "백로": "유",
        "추분": "유",
        # 술월
        "한로": "술",
        "상강": "술",
        # 해월
        "입동": "해",
        "소설": "해",
        # 자월
        "대설": "자",
        "동지": "자",
        # 축월
        "소한": "축",
        "대한": "축",
    }


# ✅ 외부에서 import 하려면 모듈 레벨 상수가 반드시 필요합니다.
TERM_TO_BRANCH = MonthBranchResolver.TERM_TO_BRANCH


def _ensure_kst(dt: datetime) -> datetime:
    """naive datetime이면 KST 부여, aware면 KST로 변환"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=KST)
    return dt.astimezone(KST)


def resolve_month_branch(loader: Optional[object], seg_start: datetime) -> str:
    """
    월지(지지)를 결정하는 함수형 헬퍼.
    - loader가 절기명 탐색을 지원하면: seg_start 기준 직전(또는 인접) 절기명으로 월지 반환
    - 그렇지 않으면: month 기반 안전 fallback
    """
    dt = _ensure_kst(seg_start)

    term_name = None
    if loader is not None:
        fn = getattr(loader, "find_adjacent_principal_term_name", None)
        if callable(fn):
            try:
                term_name = fn(dt)
            except Exception:
                term_name = None

    if isinstance(term_name, str) and term_name in TERM_TO_BRANCH:
        return TERM_TO_BRANCH[term_name]

    # ✅ fallback: 월(month) 기반 대략 매핑
    # 2월=인, 3=묘, 4=진, 5=사, 6=오, 7=미, 8=신, 9=유, 10=술, 11=해, 12=자, 1=축
    approx = {
        1: "축",
        2: "인",
        3: "묘",
        4: "진",
        5: "사",
        6: "오",
        7: "미",
        8: "신",
        9: "유",
        10: "술",
        11: "해",
        12: "자",
    }
    return approx.get(dt.month, "인")


# ✅ 클래스 메서드 형태로도 동일 API 제공 (기존 코드 호환)
def resolve(self: MonthBranchResolver, year: int, seg_start: datetime) -> str:
    # year 인자는 호환용(월지 결정은 seg_start 기준)
    return resolve_month_branch(self.loader, seg_start)


# MonthBranchResolver.resolve 를 동적으로 붙여서 기존 호출 유지
MonthBranchResolver.resolve = resolve  # type: ignore[attr-defined]
