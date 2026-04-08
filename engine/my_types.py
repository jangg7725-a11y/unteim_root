# unteim/engine/types.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, List, TypedDict
import logging
import os

# ─────────────────────────────────────────────────────────────
# 로깅 & 엄격/관용 모드 제어
# ─────────────────────────────────────────────────────────────
LOGGER = logging.getLogger("unteim")
if not LOGGER.handlers:
    # 환경변수로 로그 레벨 조정 가능: UNTEIM_LOG_LEVEL=DEBUG/INFO/...
    level = os.getenv("UNTEIM_LOG_LEVEL", "WARNING").upper()
    logging.basicConfig(level=getattr(logging, level, logging.WARNING))

def _strict_default() -> bool:
    """
    기본은 운영 모드(엄격=True).
    테스트·개발에서만 UNTEIM_STRICT_PILLARS=false 로 내려 관용 모드 사용.
    """
    v = os.getenv("UNTEIM_STRICT_PILLARS", "true").lower()
    return v in ("1", "true", "yes", "y", "on")

# ─────────────────────────────────────────────────────────────
# 기본 자료형
# ─────────────────────────────────────────────────────────────
@dataclass
class GanJi:
    gan: str
    ji: str
    def as_dict(self) -> Dict[str, str]:
        return {"gan": self.gan, "ji": self.ji}

@dataclass
class SajuPillars:
    """
    4기둥의 천간/지지를 리스트로 보관.
    gan = [year, month, day, hour]
    ji  = [year, month, day, hour]
    """
    gan: List[str]
    ji:  List[str]
    meta: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Dict[str, str]]:
        def _get(lst: List[str], i: int) -> str:
            return lst[i] if len(lst) > i else ""
        return {
            "year":  {"gan": _get(self.gan, 0), "ji": _get(self.ji, 0)},
            "month": {"gan": _get(self.gan, 1), "ji": _get(self.ji, 1)},
            "day":   {"gan": _get(self.gan, 2), "ji": _get(self.ji, 2)},
            "hour":  {"gan": _get(self.gan, 3), "ji": _get(self.ji, 3)},
        }

# ─────────────────────────────────────────────────────────────
# 신살 결과 타입(테스트/에디터 친화)
# ─────────────────────────────────────────────────────────────
class ShinsalHit(TypedDict):
    name: str      # 신살 이름
    pillar: str    # "year" | "month" | "day" | "hour"

class ShinsalResult(TypedDict):
    hits: List[ShinsalHit]
    level: str           # "none" | "minor" | "moderate" | "major"
    # 필요 시 필드 추가 가능: summary, reasons 등

# (선택) 오행 결과 타입 — 원하면 사용
class OhengResult(TypedDict, total=False):
    counts: Dict[str, int]
    tips: List[str]

# ─────────────────────────────────────────────────────────────
# 안전 변환(coerce) — 장기적 무결성 위해 엄격/관용 모드 지원
# ─────────────────────────────────────────────────────────────
def coerce_pillars(x: Any, strict: bool | None = None) -> SajuPillars:
    """
    SajuPillars 또는 {year:{gan,ji}, month:{...}, day:{...}, hour:{...}} 형태의
    매핑을 SajuPillars로 변환한다.

    strict=True(기본): 입력이 표준 형식이 아니면 예외

    strict=False: 개발/테스트 시에만 사용 (운영 비권장)
    """
    if strict is None:
        strict = _strict_default()

    if isinstance(x, SajuPillars):
        return x

    if isinstance(x, Mapping):
        def gj(key: str) -> tuple[str, str]:
            v = x.get(key, {})
            if isinstance(v, Mapping):
                return str(v.get("gan", "")), str(v.get("ji", ""))
            return "", ""

        yg, yj = gj("year")
        mg, mj = gj("month")
        dg, dj = gj("day")
        hg, hj = gj("hour")

        missing = any(not v for v in (yg, yj, mg, mj, dg, dj, hg, hj))
        if strict and missing:
            raise TypeError("Invalid pillars mapping: missing gan/ji fields in strict mode")

        

        return SajuPillars(
            [yg, mg, dg, hg],
            [yj, mj, dj, hj],
        )


    # 완전 엉뚱한 타입
    if strict:
        raise TypeError(f"Expected SajuPillars or mapping; got {type(x)}")  
    return SajuPillars([""] * 4, [""] * 4)

# ─────────────────────────────────────────────────────────────
__all__ = [
    "GanJi",
    "SajuPillars",
    "ShinsalHit",
    "ShinsalResult",
    "OhengResult",
    "coerce_pillars",
]
