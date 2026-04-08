# unteim/engine/ohengAnalyzer.py
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .types import SajuPillars, coerce_pillars

# 간단한 오행 매핑 (필요시 정확 테이블로 확장)
# 천간 10개
GAN_TO_ELEM = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}
# 지지 12개
JI_TO_ELEM = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木",
    "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水",
}


def _pillars_gan_ji(p: SajuPillars) -> Tuple[List[str], List[str]]:
    """SajuPillars에서 천간/지지 배열만 추출."""
    return p.gan, p.ji


def _count_elements(gans: List[str], jis: List[str]) -> Dict[str, int]:
    counts = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    for g in gans:
        e = GAN_TO_ELEM.get(g, "")
        if e:
            counts[e] += 1
    for j in jis:
        e = JI_TO_ELEM.get(j, "")
        if e:
            counts[e] += 1
    return counts


def _tips_from_counts(c: Dict[str, int]) -> List[str]:
    # 아주 가벼운 힌트만 (원하면 세밀화 가능)
    strongest = max(c, key=lambda k: c[k])
    weakest = min(c, key=lambda k: c[k])
    return [f"강한 오행: {strongest}, 약한 오행: {weakest}"]


def _summary_line(c: Dict[str, int]) -> str:
    # "木:2 火:3 土:2 金:1 水:0" 형태
    return " ".join([f"{k}:{c[k]}" for k in ["木", "火", "土", "金", "水"]])


def analyze_oheng(x: Any, *, strict: bool | None = None) -> Dict[str, Any]:
    """
    오행 분석 엔트리.
    - 이 단계는 기본적으로 strict=True 정책을 따르며,
    입력이 표준 형식이 아닐 경우 예외를 발생시킵니다.
    - (개발/테스트 목적에 한해 상위 레벨에서 strict=False를 명시적으로 전달할 수 있습니다)

    """
    pillars: SajuPillars = coerce_pillars(x)

    gans, jis = _pillars_gan_ji(pillars)
    counts = _count_elements(gans, jis)
    tips = _tips_from_counts(counts)
    summary = _summary_line(counts)

    return {
        "counts": counts,
        "tips": tips,
        "summary": summary,
    }
