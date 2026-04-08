# unteim/engine/sewun_engine.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Dict, Any

from .saju_pillar_adapter import get_year_pillar  # ✅ GanJi 계산(연주)


KST = ZoneInfo("Asia/Seoul")

HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


def _ensure_kst(dt: datetime) -> datetime:
    """naive면 KST로 간주, aware면 KST로 변환"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=KST)
    return dt.astimezone(KST)


def _ganji_to_str(gj) -> str:
    """
    GanJi 타입 호환:
    - gj.gan / gj.ji 가 int(0~9 / 0~11) 이면 문자로 변환
    - gj.gan / gj.ji 가 이미 "甲" "子" 문자열이면 그대로 사용
    """
    gan = getattr(gj, "gan", None)
    ji = getattr(gj, "ji", None)

    # int -> char
    if isinstance(gan, int):
        gan = HEAVENLY_STEMS[gan % 10]
    if isinstance(ji, int):
        ji = EARTHLY_BRANCHES[ji % 12]

    # None 방지
    if not isinstance(gan, str) or not isinstance(ji, str):
        raise ValueError(f"Invalid GanJi object: gan={gan!r}, ji={ji!r}")

    return f"{gan}{ji}"


@dataclass(frozen=True)
class SewoonItem:
    year: int
    year_pillar: str


class SewoonEngine:
    """
    세운(연운) 엔진:
    - 기준 datetime(dt_kst)을 받고
    - start_year ~ end_year 범위의 '연주(세운)'를 계산해 리스트로 반환
    """

    def build(self, dt_kst: datetime, start_year: int, end_year: int) -> List[SewoonItem]:
        dt_kst = _ensure_kst(dt_kst)

        items: List[SewoonItem] = []
        for y in range(int(start_year), int(end_year) + 1):
            # ✅ 해당 '연도'의 연주를 계산 (연도만 바꿔서 7/1 정오로 대표값 사용)
            #    (연주 보정 로직은 get_year_pillar 내부(= saju_core_pillars/절기)에서 처리됨)
            dt_year = dt_kst.replace(year=y, month=7, day=1, hour=12, minute=0, second=0, microsecond=0)
            gj = get_year_pillar(dt_year)
            items.append(SewoonItem(year=y, year_pillar=_ganji_to_str(gj)))
        return items

    def to_public(self, items: List[SewoonItem]) -> List[Dict[str, Any]]:
        return [{"year": it.year, "year_pillar": it.year_pillar} for it in items]
