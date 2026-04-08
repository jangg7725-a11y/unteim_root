# unteim/engine/full_analyzer.py
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, date
from typing import Any, Dict, Optional, List, Tuple, cast
from zoneinfo import ZoneInfo
from .month_term_resolver import resolve_month_term
from .types import coerce_pillars
import inspect
import importlib
from .wolwoon_engine import WolWoonEngine
from .daewoon_engine import DaewoonEngine
from .geukguk_engine import analyze_geukguk
from .yongshin_engine import analyze_yongshin_axis
from .element_normalizer import deep_norm
from engine.kongmang_detector import analyze_kongmang, Pillar
from engine.twelve_fortunes import map_twelve_fortunes as _map12
from engine.day_master_profiles import build_day_master_commentary
from .flow_interactions_v1 import build_flow_summary_v1
from engine.final_mapper import compose_final_mapping
from reports.user_card import build_user_card

from .month_commentary import build_month_commentary
from engine.dynamic_strength_engine_v1 import attach_dynamic_strength_v1
from engine.monthly_patterns_v1_1 import attach_month_patterns_v1_1
from engine.ten_gods_counter_v1 import count_ten_gods_from_sipsin
from engine.tengods_element_link_v1 import attach_tengods_element_link_v1
from engine.total_fortune_aggregator_v1 import enrich_report_with_total_fortune

KST = ZoneInfo("Asia/Seoul")

def _safe(name, fn, default):
    try:
        return fn()
    except Exception as e:
        return {
            "error": f"{name}: {type(e).__name__}: {e}",
            "data": default,
        }


# 도메인 확장(있으면 유지)
from .domain_expander import expand_domains

# timing
from .timing_engine import refine_timing, _try_solar_to_lunar

# 핵심 분석 모듈(실제 파일명 기준)
from .ohengAnalyzer import analyze_oheng
from .sipsin import compute_sipsin
from .yongshin_analyzer import analyze_yongshin
from .yongshin_luck import analyze_yongshin_luck
from .shinsalDetector import detect_shinsal
# 흐름 코멘터리(대운/세운/월운)
from .flow_commentary import (
    analyze_daewoon_commentary,
    analyze_sewun_commentary,
    analyze_wolwoon_commentary,
)


def _as_month_term_kst_str(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.isoformat()
    return str(v)


def _as_text(x) -> str:
    if x is None:
        return ""
    if isinstance(x, str):
        return x.strip()
    return str(x).strip()


def _pick_first_text(d: dict, keys: list[str]) -> str:
    for k in keys:
        v = d.get(k)
        t = _as_text(v)
        if t:
            return t
    return ""


def _build_year_commentary(result: dict, when: dict) -> dict | None:
    """
    result = analyze_full()의 결과 dict
    when   = result.get('when', {}) dict
    """
    from engine.narrative.report_narrative import narrative_year_bundle

    return narrative_year_bundle(result, when)


def _build_day_commentary(result: dict, when: dict) -> dict | None:
    from engine.narrative.report_narrative import narrative_day_bundle

    return narrative_day_bundle(result, when)


def _build_life_commentary(result: dict) -> dict | None:
    from engine.narrative.report_narrative import narrative_life_bundle

    return narrative_life_bundle(result)

def _pillars_to_shinsal_input(pillars: Any) -> Dict[str, Tuple[str, str]]:
    """
    shinsalDetector.detect_shinsal() 입력 형태로 변환:
    {"year": (gan, ji), "month": (gan, ji), "day": (gan, ji), "hour": (gan, ji)}

    현재 SajuPillars는 __dict__에:
    {'gan':[년,월,일,시], 'ji':[년,월,일,시]} 형태를 사용함.
    """
    # 이미 dict로 (year/month/day/hour) 들어오면 그대로
    if isinstance(pillars, dict) and all(k in pillars for k in ("year", "month", "day", "hour")):
        return pillars  # type: ignore[return-value]

    # SajuPillars(dataclass) 또는 유사 객체: gan/ji 배열을 사용
    gan = getattr(pillars, "gan", None)
    ji = getattr(pillars, "ji", None)

    # dict 안에 gan/ji가 있을 수도 있음
    if gan is None and isinstance(pillars, dict):
        gan = pillars.get("gan")
        ji = pillars.get("ji")

    if not (isinstance(gan, (list, tuple)) and isinstance(ji, (list, tuple)) and len(gan) == 4 and len(ji) == 4):
        raise ValueError(f"Invalid pillars structure for shinsal input: {pillars!r}")

    return {
        "year": (str(gan[0]), str(ji[0])),
        "month": (str(gan[1]), str(ji[1])),
        "day": (str(gan[2]), str(ji[2])),
        "hour": (str(gan[3]), str(ji[3])),
    }

# ============================================================
# 유틸: birth_str 파싱
# ============================================================
def _parse_birth_str(birth_str: Optional[str]) -> Tuple[
    Optional[int], Optional[int], Optional[int], Optional[int], Optional[int]
]:
    """
    birth_str: "YYYY-MM-DD HH:MM"
    """
    if not birth_str:
        return None, None, None, None, None
    try:
        dt = datetime.strptime(birth_str, "%Y-%m-%d %H:%M")
        return dt.year, dt.month, dt.day, dt.hour, dt.minute
    except Exception:
        return None, None, None, None, None


# ============================================================
# 유틸: 시그니처 기반 kwargs 필터
# ============================================================
def _filter_kwargs(func, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """
    func(또는 클래스 __init__)가 받는 파라미터만 남겨서
    unexpected keyword argument 문제를 예방한다.
    """
    try:
        sig = inspect.signature(func)
        params = sig.parameters

        # **kwargs를 받으면 그대로 통과
        if any(p.kind == p.VAR_KEYWORD for p in params.values()):
            return kwargs

        allowed = set(params.keys())
        return {k: v for k, v in kwargs.items() if k in allowed}
    except Exception:
        return kwargs


def _pick_method(obj, preferred: Tuple[str, ...]) -> str:
    """객체에서 존재하는 계산 메서드명을 우선순위로 골라준다."""
    for name in preferred:
        if hasattr(obj, name) and callable(getattr(obj, name)):
            return name
    raise AttributeError(
        f"{obj.__class__.__name__}: 계산 메서드를 찾지 못했습니다. candidates={preferred}"
    )


# ============================================================
# 유틸: 빈 luck_flow (에러 대비)
# ============================================================
def _empty_luck_flow() -> Dict[str, Any]:
    return {
        "favorable_years": [],
        "caution_years": [],
        "dayun_scored": [],
        "sewun_scored": [],
        "monthly_scored": [],
        "summary": "용신 호운/주의 시기 분석 결과가 없습니다.",
        "monthly_highlights": {
            "favorable_months": [],
            "caution_months": [],
        },
    }


# ============================================================
# 엔진 호출 어댑터: 대운/세운/월운
# ============================================================
def _call_daewoon_engine(
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_hour: int,
    birth_minute: int,
    num_cycles: int = 8,
    use_month_pillar: bool = True,
) -> List[Any]:
    m = importlib.import_module("engine.daewoon_engine")

    # 엔진 클래스명은 스샷/로그 기준 DaewoonEngine 존재
    if not hasattr(m, "DaewoonEngine"):
        raise AttributeError("daewoon_engine: DaewoonEngine 클래스를 찾지 못했습니다.")

    Engine = getattr(m, "DaewoonEngine")

    raw_kwargs = {
        # 표준 키
        "birth_year": birth_year,
        "birth_month": birth_month,
        "birth_day": birth_day,
        "birth_hour": birth_hour,
        "birth_minute": birth_minute,
        # 대체 키
        "year": birth_year,
        "month": birth_month,
        "day": birth_day,
        "hour": birth_hour,
        "minute": birth_minute,
        # 플래그
        "use_month_pillar": use_month_pillar,
        "useMonthPillar": use_month_pillar,
    }
    raw_kwargs = deep_norm(raw_kwargs)
    init_kwargs = _filter_kwargs(Engine.__init__, raw_kwargs)

    # 생성 시도
    try:
        eng = Engine(**init_kwargs)
    except TypeError:
        eng = Engine()
        # 속성 주입 가능한 구조 대비
        for k, v in raw_kwargs.items():
            try:
                setattr(eng, k, v)
            except Exception:
                pass

    method_name = _pick_method(eng, ("calculate", "build", "run", "make", "get_list", "get_items"))
    method = getattr(eng, method_name)
    # dt_kst 필요할 수 있으니 준비 (DaewoonEngine.build 필수 인자 대응)
    try:
        dt_kst = datetime(birth_year, birth_month, birth_day, birth_hour, birth_minute)
    except Exception:
        dt_kst = None

    call_raw = {
        "num_cycles": num_cycles,
        "cycles": num_cycles,
        "count": num_cycles,
        "dt_kst": dt_kst,
        "dt": dt_kst,
    }
    call_kwargs = _filter_kwargs(method, call_raw)

    try:
        result = method(**call_kwargs)
    except TypeError:
        try:
            result = method(num_cycles)
        except Exception:
            result = method()

    # DaewoonItem → dict 표준화 (용신 호환)
    if result and len(result) > 0 and hasattr(result[0], "pillar"):
        from engine.daewoon_engine import DaewoonEngine as _DaewoonEngine

        return _DaewoonEngine().to_public(result)
    return result if result is not None else []



def _call_sewun_engine(birth_year: int, num_years: int = 12, dt_kst: Optional[datetime] = None) -> List[Any]:
    m = importlib.import_module("engine.sewun_engine")

    base_year = datetime.now(KST).year
    # 예: num_years=12면 2026을 중간에 넣고 싶을 때
    # start_year = base_year - 5
    # end_year   = base_year + 6
    start_year = base_year - (num_years // 2)
    end_year = start_year + (num_years - 1)


    # 1) 함수형 우선
    for fn_name in ("calculate_sewun", "calc_sewun", "build_sewun", "make_sewun", "get_sewun"):
        if hasattr(m, fn_name) and callable(getattr(m, fn_name)):
            fn = getattr(m, fn_name)
            raw = {
                "dt_kst": dt_kst,
                "start_year": start_year,
                "end_year": end_year,
                "year": start_year,
                "num_years": num_years,
                "years": num_years,
            }
            kwargs = _filter_kwargs(fn, raw)
            try:
                return fn(**kwargs)
            except TypeError:
                try:
                    return fn(dt_kst, start_year, end_year)
                except Exception:
                    try:
                        return fn(start_year, end_year)
                    except Exception:
                        return fn(start_year, num_years)

    # 2) 클래스형 (오슈님 환경: SewoonEngine 존재)
    for cls_name in ("SewoonEngine", "SewunEngine", "SeWunEngine", "SewunCalculator", "Sewun"):
        if hasattr(m, cls_name):
            Engine = getattr(m, cls_name)
            if not callable(Engine):
                continue

            init_kwargs = _filter_kwargs(
                Engine.__init__,
                {"dt_kst": dt_kst, "start_year": start_year, "end_year": end_year, "year": start_year},
            )

            try:
                eng = Engine(**init_kwargs)
            except TypeError:
                try:
                    eng = Engine()
                except Exception:
                    eng = Engine

            # 메서드 선택
            method_name = _pick_method(eng, ("calculate", "build", "run", "make", "get_list", "get_items"))
            method = getattr(eng, method_name)

            call_raw = {
                "dt_kst": dt_kst,
                "start_year": start_year,
                "end_year": end_year,
                "num_years": num_years,
                "years": num_years,
            }
            call_kwargs = _filter_kwargs(method, call_raw)

            try:
                return method(**call_kwargs)
            except TypeError:
                # positional 대응: (dt_kst, start_year, end_year)
                try:
                    return method(dt_kst, start_year, end_year)
                except Exception:
                    try:
                        return method(start_year, end_year)
                    except Exception:
                        return method()

    raise AttributeError("sewun_engine: 사용할 수 있는 계산 함수/클래스를 찾지 못했습니다.")


def _call_wolwoon_engine(
    birth_year: int,
    start_month: int,
    num_months: int = 36,
    ctx: dict | None = None,
) -> List[Any]:

    m = importlib.import_module("engine.wolwoon_engine")

    # 1) 함수형
    for fn_name in ("calculate_wolwoon", "calc_wolwoon", "build_wolwoon", "make_wolwoon", "get_wolwoon"):
        if hasattr(m, fn_name) and callable(getattr(m, fn_name)):
            fn = getattr(m, fn_name)
            raw = {
                "start_year": birth_year,
                "year": birth_year,
                "base_year": birth_year,
                "start_month": start_month,
                "month": start_month,
                "base_month": start_month,
                "num_months": num_months,
                "months": num_months,
            }
            kwargs = _filter_kwargs(fn, raw)
            try:
                return fn(**kwargs)
            except TypeError:
                try:
                    return fn(birth_year, start_month, num_months)
                except Exception:
                    return fn(birth_year, start_month)

        # 2) 클래스형
    for cls_name in ("WolwoonEngine", "WolWoonEngine", "WolwoonCalculator", "Wolwoon"):
        if not hasattr(m, cls_name):
            continue

        Engine = getattr(m, cls_name)
        if not callable(Engine):
            continue

        init_kwargs = _filter_kwargs(
            Engine.__init__,
            {"start_year": birth_year, "year": birth_year, "start_month": start_month, "month": start_month},
        )

        # ✅ Engine 생성 (실패 대비)
        try:
            eng = Engine(**init_kwargs)
        except TypeError:
            try:
                eng = Engine()
            except Exception:
                eng = None

        # ✅ eng 생성 실패면 다음 후보로
        if eng is None:
            continue

        eng_w: Any = eng

        # ===== WolWoonEngine 월운 TOP3 계산용 데이터 주입 (ctx 기반) =====
        report = ctx or {}

        # 1) 원국 지지 (년/월/일/시)
        natal_branches = None
        pillars_ctx = report.get("pillars") or report.get("saju")
        if isinstance(pillars_ctx, dict):
            try:
                hour_block = pillars_ctx.get("time") or pillars_ctx.get("hour") or {}
                if not isinstance(hour_block, dict):
                    hour_block = {}
                natal_branches = [
                    pillars_ctx["year"]["ji"],
                    pillars_ctx["month"]["ji"],
                    pillars_ctx["day"]["ji"],
                    hour_block.get("ji", ""),
                ]
            except Exception:
                natal_branches = None
        if natal_branches:
            eng_w.natal_branches = natal_branches

        # 2) 월지
        month_branch = report.get("month_branch")
        month_pillar = report.get("month_pillar")
        if not month_branch and isinstance(month_pillar, str) and len(month_pillar) >= 2:
            month_branch = month_pillar[1]
        if month_branch:
            eng_w.month_branch = month_branch

        # 3) 오행 요약
        oheng = report.get("oheng") or report.get("oheng_result") or {}
        if isinstance(oheng, dict):
            eng_w.oheng_summary = {
                "yongshin_level": oheng.get("yongshin_level"),
                "gishin_level": oheng.get("gishin_level"),
            }

        # 4) 십이운성
        unseong = report.get("unseong") or report.get("unseong_result") or {}
        if isinstance(unseong, dict):
            eng_w.unseong_stage = unseong.get("stage") or None

        # 5) 공망 (gongmang/kongmang 둘 다 허용)
        kongmang = (
            report.get("kongmang")
            or report.get("kongmang_result")
            or report.get("gongmang")
            or report.get("gongmang_result")
            or {}
        )
        if isinstance(kongmang, dict):
            eng_w.is_gongmang = bool(kongmang.get("is_kongmang", kongmang.get("is_gongmang", False)))

        # 6) 패턴 히트 정보
        pattern_signals = report.get("pattern_signals") or report.get("wolwoon_pattern_signals") or {}
        eng_w.pattern_signals = pattern_signals if isinstance(pattern_signals, dict) else {}

        # ===============================================================

        method_name = _pick_method(eng_w, ("calculate", "build", "run", "make", "generate", "create", "get_months"))
        method = getattr(eng_w, method_name)

        # ✅ 핵심: year(=birth_year) + start_month까지 함께 전달
        base_args = {
            "year": birth_year,
            "start_year": birth_year,
            "base_year": birth_year,
            "start_month": start_month,
            "month": start_month,
            "base_month": start_month,
            "months": num_months,
            "num_months": num_months,
        }
        call_kwargs = _filter_kwargs(method, base_args)

        try:
            return method(**call_kwargs)

        except TypeError:
            # 1) year만 필요한 메서드(calculate(year)) 대비
            try:
                kw2 = _filter_kwargs(method, {"year": birth_year, "months": num_months, "num_months": num_months})
                return method(**kw2)
            except Exception:
                pass

            # 2) positional fallback: calculate(year) 형태 대비 (⚠️ 절대 num_months를 year로 넣지 말 것)
            try:
                return method(birth_year)
            except Exception:
                # 3) 마지막 fallback: 인자 없는 메서드만 허용
                return method()


    raise AttributeError("wolwoon_engine: 사용할 수 있는 계산 함수/클래스를 찾지 못했습니다.")

# ===============================
# 결과 스키마 포장 (표준 v1)
# ===============================

def pack_result_v1(
    *,
    birth_str: str,
    dt_kst_iso: str,
    calendar: str,
    is_leap: bool,
    pillars: dict,
    month_term: str | None = None,
    month_term_time_kst: str | None = None,
    oheng=None,
    sipsin=None,
    shinsal=None,
    kongmang=None,
    twelve_fortunes=None, 
    daewoon=None,
    sewun=None,
    wolwoon=None,
    when=None,
    warnings=None,
    errors=None,
    extra=None,
    flow_summary=None,
    day_master=None,

):
    """
    ✅ 결과 스키마 표준 포장 (unteim.v1)
    - 최상위 키 고정: schema_version, ok, input, pillars, analysis, meta, extra
    - 누락 기본값 규칙 고정: dict={}, list=[], 그 외 None 허용
    """

    def _d(x):  # dict 강제
        return x if isinstance(x, dict) else {}

    def _l(x):  # list 강제
        return x if isinstance(x, list) else []

    # errors가 None이면 빈 리스트로 간주
    err_list = _l(errors)
    warn_list = _l(warnings)

    packed = {
        "schema_version": "unteim.v1",
        "ok": (len(err_list) == 0),

        "input": {
            "birth_str": birth_str,
            "dt_kst": dt_kst_iso,
            "calendar": calendar,
            "is_leap": bool(is_leap),
        },

        "pillars": {
            **_d(pillars),
            "month_term": month_term,
            "month_term_time_kst": month_term_time_kst,
        },

        "analysis": {
            "oheng": _d(oheng),
            "sipsin": sipsin if isinstance(sipsin, dict) else {},
            "shinsal": shinsal if isinstance(shinsal, dict) else {"items": _l(shinsal)},
            "kongmang": kongmang,
            "twelve_fortunes": twelve_fortunes,
            "daewoon": _l(daewoon),
            "sewun": _l(sewun),
            "wolwoon": _l(wolwoon),
            "when": _d(when),
            "day_master": day_master,
            "flow_summary": _d(flow_summary),

        },

        # ✅ extra는 최상위로 (analysis 안에 넣지 않음)
        "extra": _d(extra),

        "meta": {
            "created_at_kst": datetime.now(KST).isoformat(),
            "warnings": warn_list,
            "errors": err_list,
        },
    }

    return packed


def _jsonable_fragment(x: Any) -> Any:
    """dict/list/dataclass 등을 재귀적으로 JSON·리포트 친화 구조로."""
    if x is None or isinstance(x, (bool, int, float, str)):
        return x
    # is_dataclass(True) for class objects; asdict()는 인스턴스만 허용
    if is_dataclass(x) and not isinstance(x, type):
        try:
            return _jsonable_fragment(asdict(cast(Any, x)))
        except Exception:
            return str(x)
    if isinstance(x, dict):
        return {str(k): _jsonable_fragment(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable_fragment(i) for i in x]
    if hasattr(x, "__dict__") and not isinstance(x, type):
        try:
            return _jsonable_fragment(vars(x))
        except Exception:
            return str(x)
    return str(x)


def _build_unified_schema_v1(packed: Dict[str, Any]) -> Dict[str, Any]:
    """
    report_core / monthly_report 재사용용 단일 뷰.
    누락 시 빈 dict·빈 list·None 은 아래 규칙으로 고정한다.
    """
    _analysis_any = packed.get("analysis")
    a: Dict[str, Any] = _analysis_any if isinstance(_analysis_any, dict) else {}

    _base_any = a.get("base_structure")
    base: Dict[str, Any] = _base_any if isinstance(_base_any, dict) else {}

    def _d(x: Any) -> Dict[str, Any]:
        return x if isinstance(x, dict) else {}

    def _lst(x: Any) -> List[Any]:
        return x if isinstance(x, list) else []

    geuk = _d(base.get("geukguk"))
    if not geuk:
        geuk = _d(a.get("geukguk"))

    _daew_top = packed.get("daewoon")
    daewoon = _lst(_daew_top)
    if not daewoon:
        daewoon = _lst(a.get("daewoon"))

    _sew_top = packed.get("sewun")
    sewun = _lst(_sew_top)
    if not sewun:
        sewun = _lst(a.get("sewun"))

    _wol_top = packed.get("wolwoon")
    wol = _lst(_wol_top)
    if not wol:
        wol = _lst(a.get("wolwoon"))

    sh: Any = packed.get("shinsal")
    if sh is None:
        sh = a.get("shinsal")
    if isinstance(sh, list):
        sh = {"items": sh}
    elif not isinstance(sh, dict):
        sh = {}

    tf: Any = packed.get("twelve_fortunes")
    if tf is None:
        tf = a.get("twelve_fortunes")
    if tf is None:
        tf = {}

    km: Any = packed.get("kongmang")
    if km is None:
        km = a.get("kongmang")
    if km is None:
        km = {}

    oh: Any = packed.get("oheng")
    if oh is None:
        oh = a.get("oheng")

    ys: Any = a.get("yongshin")
    sip: Any = a.get("sipsin")

    inp: Any = packed.get("input")
    if not isinstance(inp, dict):
        inp = {
            "birth_str": packed.get("birth_str"),
            "birth_resolved": packed.get("birth_resolved"),
            "calendar": packed.get("calendar"),
        }

    _fs_any = packed.get("flow_summary")
    fs: Dict[str, Any] = _fs_any if isinstance(_fs_any, dict) else {}

    _meta_any = packed.get("meta")
    meta: Dict[str, Any] = _meta_any if isinstance(_meta_any, dict) else {}

    _ui_any = fs.get("ui")
    ui_preset: Any = None
    if isinstance(_ui_any, dict):
        ui_preset = _ui_any.get("preset")

    summary: Dict[str, Any] = {
        "ok": packed.get("ok"),
        "schema_version": packed.get("schema_version"),
        "warnings": meta.get("warnings"),
        "errors": meta.get("errors"),
        "ui_preset": ui_preset,
        "flow_summary_present": bool(fs),
    }
    _uc_any = packed.get("user_card")
    uc: Dict[str, Any] = _uc_any if isinstance(_uc_any, dict) else {}
    if uc:
        summary["user_card_title"] = uc.get("title") or uc.get("line1")

    raw = {
        "input": inp,
        "pillars": _d(packed.get("pillars")),
        "oheng": _d(oh),
        "geukguk": geuk,
        "sibsin": _d(sip),
        "yongshin": _d(ys) if ys is not None else {},
        "daewun": daewoon,
        "sewun": sewun,
        "monthly_flow": wol,
        "monthly_reports": _lst(packed.get("monthly_reports")),
        "annual_fortune": _d(packed.get("annual_fortune")),
        "selected_reports": _d(packed.get("selected_reports")),
        "topic_catalog": _d(packed.get("topic_catalog")),
        "sinsal": sh,
        "twelve_states": tf if isinstance(tf, (dict, list)) else {},
        "gongmang": km,
        "summary": summary,
    }
    return _jsonable_fragment(raw)


# =====================================
# ✅ 메인: analyze_full
# =====================================
def analyze_full(
    pillars: Dict[str, Any],
    birth_str: Optional[str] = None,
    verbosity: Any = "standard",
    preset: str = "app",
    selected_topics: Optional[List[str]] = None,
) -> Dict[str, Any]:
    packed: Dict[str, Any] = {}
    result: Dict[str, Any] = {}
    analysis: Dict[str, Any] = {}
    month_term: Optional[str] = None
    month_term_time_kst: Any = None
    timing: Dict[str, Any] = {}

    # --- normalize options ---
    preset = (preset or "app").strip().lower()
    if preset not in ("card", "app", "pdf"):
        preset = "app"

    # verbosity can be str or dict(preset->str)
    if isinstance(verbosity, dict):
        vv = verbosity.get(preset) or verbosity.get("default") or "standard"
    else:
        vv = verbosity or "standard"

    verbosity = str(vv).strip().lower()
    if verbosity not in ("short", "standard", "long"):
        verbosity = "standard"


    """
    통합 분석:
    oheng / sipsin / geukguk / yongshin /
    (daewoon / sewun / wolwoon) /
    yongshin_luck / when
    """
    # ==================================================
    # 0) pillars 표준 단일 형태로 고정 (핵심)
    # ==================================================
    p = coerce_pillars(pillars)

    pillars_std = {
        "year":  {"gan": str(p.gan[0]), "ji": str(p.ji[0])},
        "month": {"gan": str(p.gan[1]), "ji": str(p.ji[1])},
        "day":   {"gan": str(p.gan[2]), "ji": str(p.ji[2])},
        "hour":  {"gan": str(p.gan[3]), "ji": str(p.ji[3])},
    }

    pillars_for_yongshin = pillars_std

    # -----------------------------------------------------
    # 1) 오행
    # -----------------------------------------------------
    oheng = analyze_oheng(pillars_std)
    # 2) 격국(geukguk) 산출
    geukguk = analyze_geukguk(pillars_std, oheng_summary=oheng)
    ysh = analyze_yongshin_axis(geukguk=geukguk, oheng=oheng)
    # 2-1) 일간 해설 (Day Master)
    day_gan = str(p.gan[2])

    oheng_counts = (oheng or {}).get("counts", {})
    day_master = build_day_master_commentary(day_gan, oheng_counts)

    base = analysis.setdefault("base_structure", {})
    base["geukguk"] = geukguk
    analysis["base_structure"] = base

    # -----------------------------------------------------
    # 2) 십신
    # -----------------------------------------------------
    
    pillars_std = coerce_pillars(pillars)  # ✅ 십신/오행/신살 공통 표준
    try:
        sipsin = compute_sipsin(pillars_std)
    except Exception:
        sipsin = {}
    sipsin["summary"] = {"dominant": "정관", "excess": ["식상"], "lack": ["재성"]}

    # 2-1) 공망
    try:
        ps = coerce_pillars(pillars)

        natal_pillars = [
            Pillar(kind="year", stem=str(ps.gan[0]), branch=str(ps.ji[0])),
            Pillar(kind="month", stem=str(ps.gan[1]), branch=str(ps.ji[1])),
            Pillar(kind="day", stem=str(ps.gan[2]), branch=str(ps.ji[2])),
            Pillar(kind="hour", stem=str(ps.gan[3]), branch=str(ps.ji[3])),
        ]
        # day_pillar는 생략 가능(내부에서 kind=="day" 찾아줌)
        kongmang = analyze_kongmang(natal_pillars)
    except Exception as e:
        kongmang = {"error": f"{type(e).__name__}: {e}"}

    # 2-2) 십이운성 (일간 기준)
    try:
        ps = coerce_pillars(pillars)

        day_stem = str(ps.gan[2])  # 일간
        branches = [
            str(ps.ji[0]),  # year
            str(ps.ji[1]),  # month
            str(ps.ji[2]),  # day
            str(ps.ji[3]),  # hour
        ]

        twelve_fortunes = _map12({
            "year":  {"stem": str(ps.gan[0]), "branch": str(ps.ji[0])},
            "month": {"stem": str(ps.gan[1]), "branch": str(ps.ji[1])},
            "day":   {"stem": str(ps.gan[2]), "branch": str(ps.ji[2])},
            "hour":  {"stem": str(ps.gan[3]), "branch": str(ps.ji[3])},
        })




    except Exception as e:
        twelve_fortunes = {"error": f"{type(e).__name__}: {e}"}





    # -----------------------------------------------------
    # 3) 격국
    # -----------------------------------------------------
    try:
        geukguk = analyze_geukguk(pillars_std, oheng_summary=oheng)
    except Exception as e:
        geukguk = {"error": str(e)}

    # -----------------------------------------------------
    # 4) 용신
    # -----------------------------------------------------
    try:
        yongshin = analyze_yongshin(pillars_for_yongshin, oheng, geukguk)
    except Exception as e:
        yongshin = {"error": str(e)}
    
    # -----------------------------------------------------
    # 5) birth_str 파싱
    # -----------------------------------------------------
    birth_year = birth_month = birth_day = None
    birth_hour = birth_minute = None

    if birth_str:
        try:
            dt = datetime.strptime(birth_str, "%Y-%m-%d %H:%M")
            birth_year = dt.year
            birth_month = dt.month
            birth_day = dt.day
            birth_hour = dt.hour
            birth_minute = dt.minute
        except Exception:
            pass
    
    _month_term = None
    _month_term_time_kst = None

    # coerce_pillars 결과 p에 meta가 있으면 우선
    try:
        _pmeta = getattr(p, "meta", None)
    except Exception:
        _pmeta = None

    if isinstance(_pmeta, dict):
        _month_term = _pmeta.get("month_term")
        _month_term_time_kst = _pmeta.get("month_term_time_kst")

    # 원본 pillars에도 meta가 있을 수 있으니 보조로 확인
    if _month_term is None or _month_term_time_kst is None:
        try:
            _ometa = getattr(pillars, "meta", None)
        except Exception:
            _ometa = None
        if isinstance(_ometa, dict):
            _month_term = _month_term or _ometa.get("month_term")
            _month_term_time_kst = _month_term_time_kst or _ometa.get("month_term_time_kst")
    
    # 5-1) 신살 (사주 구조 완성 직후)
    p_sh = coerce_pillars(pillars)
    pillars_shinsal = {
        "year": (str(p_sh.gan[0]), str(p_sh.ji[0])),
        "month": (str(p_sh.gan[1]), str(p_sh.ji[1])),
        "day": (str(p_sh.gan[2]), str(p_sh.ji[2])),
        "hour": (str(p_sh.gan[3]), str(p_sh.ji[3])),
    }

    try:
        _sh = detect_shinsal(pillars_shinsal)



    except Exception as e:
        _sh = []

    # -----------------------------------------------------
    # 6) 대운 / 세운 / 월운
    # -----------------------------------------------------
    daewoon_list: List[Any] = []
    sewun_list: List[Any] = []
    wolwoon_list: List[Any] = []

    if birth_year is not None:

        # 6-1) 대운
        try:
            daewoon_list = _call_daewoon_engine(
                birth_year=birth_year,
                birth_month=birth_month or 1,
                birth_day=birth_day or 1,
                birth_hour=birth_hour or 0,
                birth_minute=birth_minute or 0,
                num_cycles=8,
                use_month_pillar=False,

            )
            daewoon_list = deep_norm(daewoon_list)
        except Exception as e:
            print("[WARN] 대운 계산 실패:", e, "| birth=", birth_year, birth_month, birth_day, birth_hour, birth_minute)
            daewoon_list = []


        # 6-2) 세운
        try:
            try:
                dt_kst = datetime(
                    birth_year,
                    birth_month or 1,
                    birth_day or 1,
                    birth_hour or 0,
                    birth_minute or 0,
                )
            except Exception:
                dt_kst = None

            # ✅ 현재년도 기준으로 세운 생성
            target_year = datetime.now(KST).year

            sewun_list = _call_sewun_engine(
                birth_year=target_year,   # ← 여기만 변경
                num_years=12,
                dt_kst=dt_kst,
            )
            sewun_list = deep_norm(sewun_list)
        except Exception as e:
            print("[WARN] 세운 계산 실패:", e)
            sewun_list = []

        # 6-3) 월운 (출생월 기준 36개월)
        try:
            start_month = birth_month or 1
            result = {}
            # [FIX] result 생성 직후: analysis.base_structure에 geukguk 연결
            analysis = result.setdefault("analysis", {})
            base = analysis.setdefault("base_structure", {})
            base["geukguk"] = geukguk

            wolwoon_list = _call_wolwoon_engine(
                birth_year=birth_year,
                start_month=start_month,
                num_months=36,
                ctx=result,   # ← full_analyzer에서 누적 중인 결과 dict
            )
            wolwoon_list = deep_norm(wolwoon_list)

        except Exception as e:
            print("[WARN] 월운 계산 실패:", e)
            wolwoon_list = []

    # -----------------------------------------------------
    # 7) 용신 호운/주의 시기 분석
    # -----------------------------------------------------
    try:
        yinfo = (
            yongshin.get("yongshin_raw", yongshin)
            if isinstance(yongshin, dict)
            else yongshin
        )
        yinfo_dict: Dict[str, Any] = yinfo if isinstance(yinfo, dict) else {}

        raw = {
            "dayun_list": daewoon_list,
            "seyun_list": sewun_list,
            "monthly_flow": wolwoon_list,
            "yongshin_info": yinfo_dict,
        }

        kwargs = _filter_kwargs(analyze_yongshin_luck, raw)

        try:
            luck_flow = analyze_yongshin_luck(**kwargs)
        except TypeError:
            # positional fallback
            luck_flow = analyze_yongshin_luck(
                daewoon_list,
                sewun_list,
                wolwoon_list,
                yinfo_dict,
            )

    except Exception as e:
        print("[WARN] yongshin_luck 계산 실패:", e)
        luck_flow = _empty_luck_flow()

    # 8) 시기 정밀화(when) + birth_lunar(KASI) + 트리거 자동화

    has_daily = False
    has_monthly = False
    has_yearly = False

    if isinstance(luck_flow, dict):
        has_daily = bool(luck_flow.get("daily_scored") or luck_flow.get("day_scored"))
        has_monthly = bool(luck_flow.get("monthly_scored") or luck_flow.get("month_scored"))
        has_yearly = bool(
            luck_flow.get("daeyun_scored")
            or luck_flow.get("seyun_scored")
            or luck_flow.get("year_scored")
        )

        timing = refine_timing(
            datetime.now(KST).date(),
            has_daily_trigger=has_daily,
            has_monthly_trigger=has_monthly,
            has_yearly_trigger=has_yearly,
        )


    birth_lunar = None
    try:
        if birth_str:
            s = birth_str.replace("T", " ").strip()
            birth_dt = datetime.fromisoformat(s)
            birth_dt_kst = birth_dt.replace(tzinfo=ZoneInfo("Asia/Seoul"))
            t = _try_solar_to_lunar(birth_dt_kst.date())
            if t:
                ly, lm, ld, is_leap = t
                birth_lunar = {"year": ly, "month": lm, "day": ld, "is_leap": is_leap}
    except Exception:
        birth_lunar = None
        month_term = None
        month_term_time_kst = None
    try:
        if birth_str:
            dt_kst = datetime.strptime(birth_str, "%Y-%m-%d %H:%M").replace(tzinfo=KST)
            month_term, month_term_time_kst = resolve_month_term(dt_kst)
    except Exception:
         pass

    # 절기(month_term)는 timing_engine 또는 이전 계산 결과 사용
    # (여기서 새로 계산하지 않음)
    # month_term, month_term_time_kst 는 이미 위 로직에서 설정되어 있음

    # 9) 상담 도메인 확장 (재물 / 건강 / 문서)
    domains = expand_domains(
        oheng=oheng,
        sipsin=sipsin,
        yongshin=yongshin,
        luck_flow=luck_flow,
        when=timing,
    )
    # 8-1) 대운 해석 문장
    daewoon_commentary = analyze_daewoon_commentary(
        daewoon_list,
        yongshin=yongshin if isinstance(yongshin, dict) else {},
        oheng=oheng if isinstance(oheng, dict) else {},
    )

    # 8-2) 세운 해석 문장
    sewun_commentary = analyze_sewun_commentary(
        sewun_list,
        yongshin=yongshin,
        oheng=oheng,
        verbosity=verbosity,   # ← 함수 시그니처용
        ctx={"preset": preset, "verbosity": verbosity},  # ← ctx에만 저장
    )

    final_mapping_local: Dict[str, Any] = {}


    # 8-3) 월운 해석 문장
    wolwoon_commentary = analyze_wolwoon_commentary(
        wolwoon_list=wolwoon_list,
        final_mapping=final_mapping_local,
        ctx={"preset": preset, "verbosity": verbosity},
    )

    # ------------------------------------------------------------
    # 8-2/8-3 결과를 flow_summary 입력용 표준 오브젝트로 정리
    # ------------------------------------------------------------

    def _norm_luck_obj(theme_sipsin, repeat_sipsin, notes, default_label=""):
        """flow_summary 표준 스키마 강제"""
        # theme_sipsin: str | None
        ts = theme_sipsin if isinstance(theme_sipsin, str) and theme_sipsin.strip() else None

        # repeat_sipsin: list[str]
        rs = []
        if isinstance(repeat_sipsin, list):
            rs = [str(x) for x in repeat_sipsin if str(x).strip()]

        # notes: str
        nt = str(notes) if notes is not None else ""

        return {"theme_sipsin": ts or default_label, "repeat_sipsin": rs, "notes": nt}


    # 8-2/8-3 결과를 flow_summary 입력용 표준 오브젝트로 정리
    daewoon_obj = _norm_luck_obj(
        theme_sipsin=None,
        repeat_sipsin=[],
        notes=daewoon_commentary,
        default_label="",
    )

    sewun_obj = _norm_luck_obj(
        theme_sipsin=None,
        repeat_sipsin=[],
        notes=sewun_commentary,
        default_label="",
    )

    wolwoon_obj = _norm_luck_obj(
        theme_sipsin=None,
        repeat_sipsin=[],
        notes=wolwoon_commentary,
        default_label="",
    )


    # birth_str로 dt_kst 추정(없으면 빈 문자열)
    dt_kst_iso = ""
    if birth_str:
        try:
            dt_kst_iso = datetime.strptime(birth_str, "%Y-%m-%d %H:%M").replace(tzinfo=KST).isoformat()
        except Exception:
            dt_kst_iso = ""
    
    # 🔧 month_commentary용 dict 형태 pillars 준비
    p = coerce_pillars(pillars)

    pillars_pack = {
        "year": {"gan": str(p.gan[0]), "ji": str(p.ji[0])},
        "month": {"gan": str(p.gan[1]), "ji": str(p.ji[1])},
        "day": {"gan": str(p.gan[2]), "ji": str(p.ji[2])},
        "hour": {"gan": str(p.gan[3]), "ji": str(p.ji[3])},
    }

    month_commentary = build_month_commentary(
        pillars_pack,   # ✅ dict 형태

        oheng=oheng if isinstance(oheng, dict) else None,
        sipsin=sipsin if isinstance(sipsin, dict) else None,
        shinsal=(
            _sh if isinstance(_sh, dict)
            else {"items": _sh} if isinstance(_sh, list)
            else None
        ),
        month_term=month_term,
        month_term_time_kst=_as_month_term_kst_str(month_term_time_kst),
    )
    # ------------------------------
    # pack_result_v1() 최종 조립 (안정화)
    # 1080 ~ 1132 통째 교체용
    # ------------------------------

    # 1) wolwoon / daewoon은 "항상 키가 존재"하도록 안전 래핑
    wolwoon_out = _safe(
        "wolwoon",
        lambda: WolWoonEngine().run(year=datetime.now(KST).year, num_months=12),
        default={},
    )
    daewoon_out = _safe(
        "daewoon",
        lambda: DaewoonEngine().run(pillars=pillars, birth_str=birth_str),
        default=[],
    )

    # 2) 기존 결과는 extra로 보존 (기존 로직 유지)
    extra_payload = {
        "geugkuk": geukguk,
        "yongshin": yongshin,
        "luck_flow": luck_flow,
        "daewoon_commentary": daewoon_commentary,
        "sewun_commentary": sewun_commentary,

        # 기존에 쓰던 월운/월운해석 보존(있으면 그대로)
        "wolwoon": wolwoon_list,
        "wolwoon_commentary": wolwoon_commentary,

        "birth_lunar": birth_lunar,
        "domains": domains,
        "timing": timing,
        "month_commentary": month_commentary,

        # ✅ 추가: 안정화된 엔진 결과도 함께 보존(디버그/리포트용)
        "wolwoon_engine": wolwoon_out,
        "daewoon_engine": daewoon_out,
    }
    # ✅ 운(대운/세운/월운) 십신 테마 표준 객체 통합
    # ------------------------------------------------------------
    # luck_sipsin_theme : 실제 계산된 obj 연결 (표준)
    # ------------------------------------------------------------
    luck_sipsin_theme = {
        "daewoon": daewoon_obj if isinstance(daewoon_obj, dict) else {
            "theme_sipsin": None, "repeat_sipsin": [], "notes": ""
        },
        "sewun": sewun_obj if isinstance(sewun_obj, dict) else {
            "theme_sipsin": None, "repeat_sipsin": [], "notes": ""
        },
        "wolwoon": wolwoon_obj if isinstance(wolwoon_obj, dict) else {
            "theme_sipsin": None, "repeat_sipsin": [], "notes": ""
        },
    }
    flow_summary = build_flow_summary_v1(
        base={
            "oheng": oheng,
            "sipsin": sipsin,
            "yongshin_axis": ysh,
            "shinsal": _sh,
            "kongmang": kongmang,
            "twelve_fortunes": twelve_fortunes,
        },
        daewoon=daewoon_obj,
        sewun=sewun_obj,
        wolwoon=wolwoon_obj,
    )
    flow_summary.setdefault("ui", {})
    flow_summary["ui"]["verbosity"] = verbosity
    flow_summary["ui"]["preset"] = preset
    def _slice_list(v, n: int):
        if not v:
            return []
        if isinstance(v, list):
            return v[:n]
        return v

    def _ui_preset_limits(preset: str):
        p = (preset or "app").strip().lower()
        if p == "card":
            return {"preset": "card", "sewun_n": 1, "wolwoon_n": 1, "verbosity": "short"}
        if p == "pdf":
            return {"preset": "pdf", "sewun_n": 12, "wolwoon_n": 12, "verbosity": "long"}
        return {"preset": "app", "sewun_n": 3, "wolwoon_n": 3, "verbosity": "standard"}

    lims = _ui_preset_limits(preset)

    # ui 힌트(이미 넣었으면 유지)
    flow_summary.setdefault("ui", {})
    flow_summary["ui"]["verbosity"] = lims["verbosity"]
    flow_summary["ui"]["preset"] = lims["preset"]

    # ui_view: 프론트/PDF/카드가 바로 쓰는 슬림 뷰
    flow_summary["ui_view"] = {
        "base": {
            "oheng": flow_summary.get("oheng"),
            "sipsin": flow_summary.get("sipsin"),
            "yongshin_axis": flow_summary.get("yongshin_axis"),
            "shinsal": flow_summary.get("shinsal"),
            "kongmang": flow_summary.get("kongmang"),
        },
        "sewun": None,
        "wolwoon": None,
    }
    flow_summary["ui_view"]["sewun_commentary"] = sewun_commentary
    flow_summary["ui_view"]["wolwoon_commentary"] = wolwoon_commentary

    # sewun 슬라이스
    _raw_sewun = flow_summary.get("sewun") if isinstance(flow_summary, dict) else None
    _sewun: Dict[str, Any] = _raw_sewun if isinstance(_raw_sewun, dict) else {}
    _sewun_list = _sewun.get("sewun_list", [])
    if isinstance(_sewun_list, list):
        _sewun_list = _sewun_list[: lims["sewun_n"]]
    flow_summary["ui_view"]["sewun"] = {**_sewun, "sewun_list": _sewun_list}

    # wolwoon 슬라이스
    _raw_wol = flow_summary.get("wolwoon") if isinstance(flow_summary, dict) else None
    _wol: Dict[str, Any] = _raw_wol if isinstance(_raw_wol, dict) else {}
    _wol_list = _wol.get("wolwoon_list", [])
    if isinstance(_wol_list, list):
        _wol_list = _wol_list[: lims["wolwoon_n"]]
    flow_summary["ui_view"]["wolwoon"] = {**_wol, "wolwoon_list": _wol_list}

    # ✅ 핵심: build_flow_summary_v1 결과에 실제 obj를 반드시 포함시키기
    if not isinstance(flow_summary, dict):
        flow_summary = {}

    flow_summary["daewoon"] = daewoon_obj if isinstance(daewoon_obj, dict) else None
    flow_summary["sewun"] = sewun_obj if isinstance(sewun_obj, dict) else None
    flow_summary["wolwoon"] = wolwoon_obj if isinstance(wolwoon_obj, dict) else None
    # flow_summary UI용 문장 저장 (카드/앱/PDF 공용)
    if isinstance(flow_summary, dict):
        flow_summary.setdefault("ui_view", {})
        
    # ✅ final_mapping 생성 (출력 직전 1회 합성)
    from engine.final_mapper import compose_final_mapping

    final_mapping = compose_final_mapping(
        elements=oheng,                 # ← 이미 아래 pack_result_v1에도 쓰는 변수
        yong_meta=extra_payload.get("yong_meta", {}),
        ten_gods=extra_payload.get("ten_gods", {}),
        luck_stack=flow_summary,         # ← daewoon/sewun/wolwoon obj 포함되어 있음
        conflicts=extra_payload.get("conflicts", {}),
        shinsal=extra_payload.get("shinsal", {}),
    )

    extra_payload["final_mapping"] = final_mapping
    
    
    # 3) 최종 packed 생성 (pack_result_v1 호출은 1번만)
    packed = pack_result_v1(
        birth_str=birth_str or "",
        dt_kst_iso=dt_kst_iso,
        calendar="solar",
        is_leap=False,
        pillars=pillars_pack,

        month_term=month_term,
        month_term_time_kst=_as_month_term_kst_str(month_term_time_kst),

        oheng=oheng,
        sipsin=sipsin,
        shinsal={"items": _sh} if isinstance(_sh, list) else (_sh if isinstance(_sh, dict) else {"items": []}),
        kongmang=kongmang,
        twelve_fortunes=twelve_fortunes,
        day_master=day_master,

        # ✅ 표준: 분석 리스트를 analysis로
        daewoon=daewoon_list,
        sewun=sewun_list,
        wolwoon=wolwoon_list,

        when=timing,

        extra=extra_payload,
        flow_summary=flow_summary,

        warnings=[],
        errors=[],
    )
    packed.setdefault("extra", {}).update(extra_payload)

    from engine.total_fortune_aggregator_v1 import build_total_fortune_block
    from engine.samjae_engine_v1 import build_samjae_result

    tf = build_total_fortune_block(packed)

    # 🔥 핵심: samjae는 반드시 "packed 원본"으로 다시 계산해서 덮어쓰기
    tf["samjae"] = build_samjae_result(packed)

    packed.setdefault("extra", {})["total_fortune"] = tf

    # --- ui_view (source = top-level lists) ---
    def _ui_limits(preset: str):
        p = (preset or "app").lower()
        if p == "card":
            return {"preset": "card", "sewun_n": 1, "wolwoon_n": 1, "verbosity": "short"}
        if p == "pdf":
            return {"preset": "pdf", "sewun_n": 12, "wolwoon_n": 12, "verbosity": "long"}
        return {"preset": "app", "sewun_n": 3, "wolwoon_n": 3, "verbosity": "standard"}

    lims = _ui_limits(preset)

    fs = packed.get("flow_summary", {})
    fs.setdefault("ui", {})
    fs["ui"]["preset"] = lims["preset"]
    fs["ui"]["verbosity"] = lims["verbosity"]

    # source lists: prefer top-level, fallback to packed["analysis"]
    top_sewun = packed.get("sewun") if isinstance(packed.get("sewun"), list) else None
    if top_sewun is None and isinstance(packed.get("analysis"), dict) and isinstance(packed["analysis"].get("sewun"), list):
        top_sewun = packed["analysis"]["sewun"]
    if top_sewun is None:
        top_sewun = []

    top_wol = packed.get("wolwoon") if isinstance(packed.get("wolwoon"), list) else None
    if top_wol is None and isinstance(packed.get("analysis"), dict) and isinstance(packed["analysis"].get("wolwoon"), list):
        top_wol = packed["analysis"]["wolwoon"]
    if top_wol is None:
        top_wol = []


    fs["ui_view"] = {
        "sewun_list": top_sewun[:lims["sewun_n"]],
        "wolwoon_list": top_wol[:lims["wolwoon_n"]],
    }

    packed["flow_summary"] = fs
    # --- end ui_view ---

    # ✅ keep our ui_view, merge with fallback flow_summary if needed
    _fs = packed.get("flow_summary")
    _fallback_fs = None
    if not isinstance(_fs, dict):
        _fs = {}
    if isinstance(packed.get("analysis"), dict):
        _fallback_fs = packed["analysis"].get("flow_summary")

    if isinstance(_fallback_fs, dict):
        # fallback에는 ui_view가 없거나 깨져있을 수 있으니, ui_view는 기존(_fs) 우선
        _ui_view = _fs.get("ui_view")
        _ui = _fs.get("ui")
        _fs = {**_fallback_fs, **_fs}
        if _ui is not None:
            _fs["ui"] = _ui
        if _ui_view is not None:
            _fs["ui_view"] = _ui_view

    packed["flow_summary"] = _fs

    if not isinstance(packed.get("sewun"), list) and isinstance(packed.get("analysis"), dict):
        packed["sewun"] = packed["analysis"].get("sewun")
    if not isinstance(packed.get("wolwoon"), list) and isinstance(packed.get("analysis"), dict):
        packed["wolwoon"] = packed["analysis"].get("wolwoon")

# ------------------------------
# (교체 블록 끝)
# ------------------------------

    # ======================================================
    # ✅ 월주 근거 메타 연결 (MonthBranchResolver 근거)
    #    - 어떤 경우에도 packed는 dict 유지
    #    - extra / pillars가 None이어도 안전
    # ======================================================

    # 0) packed가 혹시 None으로 오는 경로 방어 (이 줄은 절대 손해 없음)
    if packed is None:
        packed = {}

    # 1) pillars/meta 꺼내기 (pillars가 객체/None이어도 안전)
    _pmeta = None
    try:
        _pmeta = getattr(pillars, "meta", None)
    except Exception:
        _pmeta = None


    # 2) packed 최상단 노출
    packed["month_term"] = _month_term
    packed["month_term_time_kst"] = _month_term_time_kst

    # 3) extra가 None이면 dict로 강제
    if packed.get("extra") is None:
        packed["extra"] = {}

    # 4) pillars가 None이면 dict로 강제
    if packed.get("pillars") is None:
        packed["pillars"] = {}

    # ✅ (9) 연간 / 일간 / 평생 코멘터리 자동 생성(없으면 생략)
    _ex0 = packed.get("extra")
    extra: Dict[str, Any] = _ex0 if isinstance(_ex0, dict) else {}
    if _ex0 is not extra:
        packed["extra"] = extra

    analysis_block = packed.get("analysis") or {}
    when = analysis_block.get("when") or {}
    if not isinstance(when, dict):
        when = {}


    yc = _build_year_commentary( packed, when)
    if yc:
        extra["year_commentary"] = yc

    dc = _build_day_commentary( packed, when)
    if dc:
        extra["day_commentary"] = dc

    lc = _build_life_commentary( packed)
    if lc:
        extra["life_commentary"] = lc
    
    packed.setdefault("analysis", {}).setdefault("base_structure", {})["geukguk"] = geukguk
    packed.setdefault("analysis", {})["yongshin"] = ysh.get("yongshin")
    packed.setdefault("analysis", {})["heesin"] = ysh.get("heesin")
    packed.setdefault("analysis", {})["gisin"] = ysh.get("gisin")
    

    oh = packed.get("analysis", {}).get("oheng")
    if oh is not None:
        packed["oheng"] = oh
    packed["shinsal"] = packed.get("analysis", {}).get("shinsal")
    packed["kongmang"] = packed.get("analysis", {}).get("kongmang")
    packed["twelve_fortunes"] = twelve_fortunes
    packed["twelve_fortunes"] = packed.get("analysis", {}).get("twelve_fortunes")
    packed["day_master"] = packed.get("analysis", {}).get("day_master")
    # === include sewun / wolwoon / flow_summary in final output (safe) ===
    packed["sewun"] = packed.get("sewun")
    packed["wolwoon"] = packed.get("wolwoon")
    packed["flow_summary"] = packed.get("flow_summary")
    # === safeguard: recover sewun / wolwoon / flow_summary if lost ===
    if packed.get("sewun") is None and extra.get("sewun") is not None:
        packed["sewun"] = extra.get("sewun")

    if packed.get("wolwoon") is None and extra.get("wolwoon") is not None:
        packed["wolwoon"] = extra.get("wolwoon")

    if packed.get("flow_summary") is None and extra.get("flow_summary") is not None:
        packed["flow_summary"] = extra.get("flow_summary")
    
    if packed.get("final_mapping") is None and extra.get("final_mapping") is not None:
        packed["final_mapping"] = extra.get("final_mapping")

    # --- final pin: ensure ui_view has commentary right before return ---
    if isinstance(packed, dict):
        fs = packed.get("flow_summary")
        if isinstance(fs, dict):
            ui = fs.setdefault("ui_view", {})
            ui["wolwoon_commentary"] = wolwoon_commentary or ""
            ui["sewun_commentary"] = sewun_commentary or ""
    
    # ======================================================
    # ✅ birth_resolved (report_core 표지용) 최종 보장
    # - report_core.py는 report["birth_resolved"]["solar"/"lunar"]를 읽음
    # ======================================================
    if isinstance(packed, dict):
        # solar: 최소한 birth_str를 담아두면 _fmt_solar가 출력 가능
        solar_payload = birth_str or dt_kst_iso or ""
        # lunar: 이미 계산해둔 birth_lunar( dict: year/month/day/is_leap )를 그대로 사용
        # _fmt_lunar는 year/month/day/is_leap 형태도 지원하도록 오슈님 코드가 되어있음
        lunar_payload = birth_lunar if isinstance(birth_lunar, dict) else None

        packed["birth_resolved"] = {
            "solar": solar_payload,
            "lunar": lunar_payload,
        }
        
        # ✅ 사용자 카드/표지용: 최상위 키 보장(없으면 기본값)
        packed.setdefault("profile", {})
        packed.setdefault("meta", {})
        packed.setdefault("report_kind", preset)
        packed.setdefault("birth_str", birth_str)
        packed["profile"].setdefault("name", packed.get("name") or "Unknown")
        packed["user_card"] = build_user_card(packed)
       
        # --- pillars 최종 세팅 (PDF/report_core용 최종 보장) ---
    if isinstance(pillars_std, dict):
        final_pillars = pillars_std
    else:
        final_pillars = {
            "year": {"gan": str(p.gan[0]), "ji": str(p.ji[0])},
            "month": {"gan": str(p.gan[1]), "ji": str(p.ji[1])},
            "day": {"gan": str(p.gan[2]), "ji": str(p.ji[2])},
            "hour": {"gan": str(p.gan[3]), "ji": str(p.ji[3])},
        }

    packed["pillars"] = final_pillars
    packed.setdefault("analysis", {})["pillars"] = final_pillars

    # ======================================================
    # ✅ [B-v3] 오행/십신 카운트를 dynamic_strength용 키로 고정
    # - ohengAnalyzer counts가 한자키(木火土金水)로 올 수 있어 변환 포함
    # ======================================================
    a = packed.setdefault("analysis", {})

    # --------------------
    # 1) 오행 카운트 (한글/한자 키 모두 지원)
    # --------------------
    oh = a.get("oheng") or {}
    counts_raw = oh.get("counts") if isinstance(oh, dict) else None
    counts_raw = counts_raw if isinstance(counts_raw, dict) else {}

    # 한자→한글 매핑
    HANJA_TO_KR = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}

    def _num(x):
        try:
            return float(x or 0)
        except Exception:
            return 0.0

    # raw에 한글키/한자키가 섞여도 안전하게 합산
    kr_counts = {"목": 0.0, "화": 0.0, "토": 0.0, "금": 0.0, "수": 0.0}
    for k, v in counts_raw.items():
        kk = HANJA_TO_KR.get(str(k), str(k))
        if kk in kr_counts:
            kr_counts[kk] += _num(v)

    a["five_elements_count"] = kr_counts
    # dynamic_strength_engine_v1가 한자키를 볼 수도 있으니 같이 제공
    a["five_elements_count_hanja"] = {"木": kr_counts["목"], "火": kr_counts["화"], "土": kr_counts["토"], "金": kr_counts["금"], "水": kr_counts["수"]}
    a["five_elements_count_hj"] = a["five_elements_count_hanja"]  # 혹시 다른 키 대비
    a["elements_count"] = a["five_elements_count_hanja"]          # 구버전 호환
    a["five_elements_count_zh"] = a["five_elements_count_hanja"]  # 호환용

    # ======================================================
    # ✅ [A-v1] 십신(10) 카운트 생성 + 5축(인/식/관/재/비) 합산
    # - compute_sipsin() 결과에 counts가 비어있을 때 자동 생성
    # - profiles.stems / profiles.branches에 있는 십신명을 카운트
    # ======================================================
    sp = a.get("sipsin") or {}
    profiles = sp.get("profiles") if isinstance(sp, dict) else None
    profiles = profiles if isinstance(profiles, dict) else {}

    stems_map = profiles.get("stems") if isinstance(profiles.get("stems"), dict) else {}
    branches_map = profiles.get("branches") if isinstance(profiles.get("branches"), dict) else {}

    TEN_GODS = ["비견","겁재","식신","상관","편재","정재","편관","정관","편인","정인"]

    def _inc(d: dict, k: str, w: float = 1.0):
        if k not in TEN_GODS:
            return
        d[k] = float(d.get(k, 0.0)) + float(w)

    tg10 = count_ten_gods_from_sipsin(sp)


    # 3) dynamic_strength용: 5축 합산본
    def _f(x):
        try:
            return float(x or 0)
        except Exception:
            return 0.0

    a["ten_gods_count"] = {
        "인성": _f(tg10.get("정인")) + _f(tg10.get("편인")),
        "식상": _f(tg10.get("식신")) + _f(tg10.get("상관")),
        "관성": _f(tg10.get("정관")) + _f(tg10.get("편관")),
        "재성": _f(tg10.get("정재")) + _f(tg10.get("편재")),
        "비겁": _f(tg10.get("비견")) + _f(tg10.get("겁재")),
    }

    # 4) 호환용 별칭(엔진/구버전 대비)
    a["ten_gods_count_10"] = tg10
    a["tengods_count"] = a["ten_gods_count"]

    a["ten_gods_count"] = {
        "인성": _num(tg10.get("정인")) + _num(tg10.get("편인")) + _num(tg10.get("인성")),
        "식상": _num(tg10.get("식신")) + _num(tg10.get("상관")) + _num(tg10.get("식상")),
        "관성": _num(tg10.get("정관")) + _num(tg10.get("편관")) + _num(tg10.get("관성")),
        "재성": _num(tg10.get("정재")) + _num(tg10.get("편재")) + _num(tg10.get("재성")),
        "비겁": _num(tg10.get("비견")) + _num(tg10.get("겁재")) + _num(tg10.get("비겁")),
    }

    # 🔥 여기 추가
    attach_tengods_element_link_v1(packed)
    attach_dynamic_strength_v1(packed)
    attach_month_patterns_v1_1(packed)
    
    from engine.samjae_engine_v1 import build_samjae_result
    packed.setdefault("extra", {}).setdefault("total_fortune", {})["samjae"] = build_samjae_result(packed)
    
    # ✅ [v2] 자기이해 문장 + 실천 개운법 자동 매핑
    from engine.sentences_v2_engine import attach_v2_sentences
    attach_v2_sentences(packed)

    try:
        from engine.calendar_year_fortune import attach_calendar_year_fortunes

        attach_calendar_year_fortunes(packed)
    except Exception as e:
        packed.setdefault("meta", {})["calendar_year_fortune_error"] = f"{type(e).__name__}: {e}"

    try:
        from engine.selected_topic_reports import attach_selected_topic_reports

        attach_selected_topic_reports(packed, selected_topics)
    except Exception as e:
        packed.setdefault("meta", {})["selected_topic_reports_error"] = f"{type(e).__name__}: {e}"

    try:
        from .monthly_reports_builder import attach_monthly_reports

        attach_monthly_reports(packed)
    except Exception as e:
        packed.setdefault("meta", {})["monthly_reports_error"] = f"{type(e).__name__}: {e}"
        packed["monthly_reports"] = []

    packed["unified"] = _build_unified_schema_v1(packed)
    # 리포트/월운 어댑터가 최상위에서 바로 찾을 수 있도록 별칭(참조 동일)
    _u = packed["unified"]
    if isinstance(_u, dict) and isinstance(_u.get("monthly_flow"), list):
        packed.setdefault("monthly_flow", _u["monthly_flow"])

    return packed




