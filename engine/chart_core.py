# unteim/engine/chart_core.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .types import SajuPillars, coerce_pillars


def _birth_str_from_res(res: Dict[str, Any]) -> str:
    for key in ("birth_str", "birth", "input"):
        v = res.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
        if isinstance(v, dict):
            for k2 in ("birth", "birth_str"):
                s = v.get(k2)
                if isinstance(s, str) and s.strip():
                    return s.strip()
    return ""


def _pillar_pair(src: Any) -> Dict[str, str]:
    if isinstance(src, dict):
        g = src.get("gan") or src.get("stem") or ""
        j = src.get("ji") or src.get("branch") or ""
        return {"gan": str(g), "ji": str(j)}
    return {"gan": "", "ji": ""}


def _pillars_stem_branch(pd: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    """sipsin.map_sipsin / geukguk_analyzer 호환: stem · branch 키."""
    out: Dict[str, Dict[str, str]] = {}
    for k in ("year", "month", "day", "hour"):
        v = pd.get(k) or {}
        out[k] = {
            "stem": str(v.get("gan") or v.get("stem") or ""),
            "branch": str(v.get("ji") or v.get("branch") or ""),
        }
    return out


def _oheng_counts(oheng: Dict[str, Any]) -> Dict[str, Any]:
    """격국 분석 등에서 기대하는 오행 건수 dict."""
    if not isinstance(oheng, dict):
        return {}
    c = oheng.get("counts")
    return c if isinstance(c, dict) else oheng


class _GeukCtxAdapter:
    """geukguk_analyzer: ctx.get('pillars') 와 ctx.pillars 속성 접근을 모두 만족."""

    __slots__ = ("_pillars", "oheng", "sibsin")

    def __init__(
        self,
        pillars_stem_branch: Dict[str, Dict[str, str]],
        oheng_counts: Dict[str, Any],
        sibsin_counts: Dict[str, Any],
    ) -> None:
        self._pillars: Dict[str, Any] = {**pillars_stem_branch, "hidden_stems": {}}
        self.oheng = oheng_counts
        self.sibsin = sibsin_counts

    @property
    def pillars(self) -> Dict[str, Any]:
        return self._pillars

    def get(self, key: str, default: Any = None) -> Any:
        if key == "pillars":
            return self._pillars
        if key == "sipsin_detail":
            return None
        return getattr(self, key, default)


@dataclass
class ChartContext:
    """
    운트임 사주 한 벌에 대한 '공통 컨텍스트' 묶음.

    - birth_str      : "YYYY-MM-DD HH:MM" (KST)
    - pillars        : SajuPillars (연/월/일/시 간지 리스트)
    - pillars_dict   : {"year":{"gan","ji"}, ...} 원본 딕셔너리
    - oheng          : 오행 분석 결과 (ohengAnalyzer 출력)
    - shinsal        : 신살 분석 결과 (shinsalDetector 출력)

    아래 필드들은 있으면 채우고, 에러가 나면 None 으로 둔다.
    - sibsin         : 십신 매핑/요약
    - twelve_fortunes: 12운성 결과
    - geukguk        : 격국 분석
    - yongshin       : 용신/희신/기신 분석
    - sipsin         : 십신 심화 프로필
    """
    birth_str: str
    pillars: SajuPillars
    pillars_dict: Dict[str, Dict[str, str]]

    oheng: Dict[str, Any]
    shinsal: Dict[str, Any]

    sibsin: Optional[Dict[str, Any]] = None
    twelve_fortunes: Optional[Dict[str, Any]] = None
    geukguk: Optional[Dict[str, Any]] = None
    yongshin: Optional[Dict[str, Any]] = None
    sipsin: Optional[Any] = None


def _extract_pillars_from_result(res: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """
    분석 번들 dict에서 연/월/일/시 간지를 {gan, ji}로 통일.
    (키 누락 시 빈 문자열)
    """
    return {k: _pillar_pair(res.get(k)) for k in ("year", "month", "day", "hour")}


def build_chart_context(res: Dict[str, Any]) -> ChartContext:
    """
    calculate_saju() 결과(res)를 받아서
    오행/신살/십신/12운성/격국/용신/십신심화까지
    한 번에 채운 ChartContext 를 만들어 돌려준다.
    """
    pillars_dict = _extract_pillars_from_result(res)

    # SajuPillars 객체로 변환 (strict=False: 필드 조금 틀려도 일단 맞춰줌)
    pillars = coerce_pillars(pillars_dict)

    ctx = ChartContext(
        birth_str=_birth_str_from_res(res),
        pillars=pillars,
        pillars_dict=pillars_dict,
        oheng=res.get("oheng", {}) or {},
        shinsal=res.get("shinsal", {}) or {},
    )

    # ───────────────────────
    # 1) 십신(건수) / 12운성
    # ───────────────────────
    try:
        from engine.sipsin import compute_sipsin

        _sip = compute_sipsin(pillars)
        prof = _sip.get("profiles") if isinstance(_sip, dict) else None
        ctx.sibsin = (prof.get("counts") if isinstance(prof, dict) else None) or {}
    except Exception:
        ctx.sibsin = {}

    try:
        # 60갑자×12운성 완전 테이블 쪽에 맞춰 사용
        from .twelve_fortunes import map_twelve_fortunes

        ctx.twelve_fortunes = map_twelve_fortunes(pillars_dict)
    except Exception:
        ctx.twelve_fortunes = None

    # ───────────────────────
    # 2) 격국 / 용신 / 십신 심화
    # ───────────────────────
    try:
        from .geukguk_analyzer import analyze_geukguk

        stem_br = _pillars_stem_branch(pillars_dict)
        geuk_in = _GeukCtxAdapter(
            stem_br,
            _oheng_counts(ctx.oheng),
            ctx.sibsin if isinstance(ctx.sibsin, dict) else {},
        )
        ctx.geukguk = analyze_geukguk(geuk_in)
    except Exception:
        ctx.geukguk = None

    try:
        from .yongshin_analyzer import analyze_yongshin

        ctx.yongshin = analyze_yongshin(
            ctx.pillars_dict,
            ctx.oheng,
            ctx.geukguk if isinstance(ctx.geukguk, dict) else {},
        )
    except Exception:
        ctx.yongshin = None

    try:
        from .sipsin_profile import analyze_sipsin_profiles

        ctx.sipsin = analyze_sipsin_profiles(ctx)
    except Exception:
        ctx.sipsin = None

    return ctx
