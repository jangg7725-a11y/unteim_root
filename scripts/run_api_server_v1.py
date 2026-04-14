# unteim/scripts/run_api_server_v1.py
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(_ROOT)

try:
    from dotenv import load_dotenv  # type: ignore[import-untyped]

    load_dotenv(os.path.join(_ROOT, ".env"))
except ImportError:
    pass

from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, cast

from fastapi import FastAPI, HTTPException  # type: ignore[import-untyped]
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import-untyped]
from fastapi.responses import FileResponse, JSONResponse  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field  # type: ignore[import-untyped]

from engine.sajuCalculator import calculate_saju
from engine.full_analyzer import analyze_full
from engine.counsel_service import run_counsel_turn
from engine.compatibility_analyzer import analyze_compatibility
from engine.solo_love_insight import build_solo_love_insight
from engine.hidden_stems import compute_hidden_stems
from engine.sipsin import ten_god_stem
from reports.monthly_report import build_monthly_report_pdf
import traceback


# -------------------------
# 고정 출력 경로 (1개로 통일)
# -------------------------
OUT_PDF = Path("out") / "monthly_report.pdf"

_STEM_EL_YY: dict[str, tuple[str, str]] = {
    "甲": ("목", "+"), "乙": ("목", "-"), "丙": ("화", "+"), "丁": ("화", "-"),
    "戊": ("토", "+"), "己": ("토", "-"), "庚": ("금", "+"), "辛": ("금", "-"),
    "壬": ("수", "+"), "癸": ("수", "-"),
}
_BRANCH_EL_YY: dict[str, tuple[str, str]] = {
    "子": ("수", "+"), "丑": ("토", "-"), "寅": ("목", "+"), "卯": ("목", "-"),
    "辰": ("토", "+"), "巳": ("화", "-"), "午": ("화", "+"), "未": ("토", "-"),
    "申": ("금", "+"), "酉": ("금", "-"), "戌": ("토", "+"), "亥": ("수", "-"),
}
_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


def _void_by_pillar(stem: str, branch: str) -> str:
    idx = -1
    for i in range(60):
        if _STEMS[i % 10] == stem and _BRANCHES[i % 12] == branch:
            idx = i
            break
    if idx < 0:
        return "—"
    groups = ["戌亥", "申酉", "午未", "辰巳", "寅卯", "子丑"]
    return groups[idx // 10]


def _build_saju_overview(engine_result: dict[str, Any]) -> dict[str, Any]:
    pillars = engine_result.get("pillars") if isinstance(engine_result.get("pillars"), dict) else {}
    analysis = engine_result.get("analysis") if isinstance(engine_result.get("analysis"), dict) else {}

    year = pillars.get("year") if isinstance(pillars.get("year"), dict) else {}
    month = pillars.get("month") if isinstance(pillars.get("month"), dict) else {}
    day = pillars.get("day") if isinstance(pillars.get("day"), dict) else {}
    hour = pillars.get("hour") if isinstance(pillars.get("hour"), dict) else {}

    pnorm = {
        "year": {"stem": str(year.get("gan") or ""), "branch": str(year.get("ji") or "")},
        "month": {"stem": str(month.get("gan") or ""), "branch": str(month.get("ji") or "")},
        "day": {"stem": str(day.get("gan") or ""), "branch": str(day.get("ji") or "")},
        "hour": {"stem": str(hour.get("gan") or ""), "branch": str(hour.get("ji") or "")},
    }
    day_stem = pnorm["day"]["stem"]
    hidden = compute_hidden_stems(pnorm)

    tf = analysis.get("twelve_fortunes") if isinstance(analysis.get("twelve_fortunes"), dict) else {}
    sh = analysis.get("shinsal") if isinstance(analysis.get("shinsal"), dict) else {}
    sh_items = sh.get("items") if isinstance(sh.get("items"), list) else []

    by_where_shinsal: dict[str, list[str]] = {"year": [], "month": [], "day": [], "hour": []}
    for it in sh_items:
        if not isinstance(it, dict):
            continue
        w = str(it.get("where") or "").strip()
        n = str(it.get("name") or "").strip()
        if w in by_where_shinsal and n and ("12운성" not in n) and (not n.startswith("12")):
            by_where_shinsal[w].append(n)
    for k in by_where_shinsal:
        # 중복 제거 + 기둥별 최대 8개 노출(누락 체감 방지)
        uniq = []
        seen = set()
        for x in by_where_shinsal[k]:
            if x not in seen:
                seen.add(x)
                uniq.append(x)
        by_where_shinsal[k] = uniq[:8]

    pillars_out: dict[str, Any] = {}
    yin_yang_counts: dict[str, int] = {"+목": 0, "-목": 0, "+화": 0, "-화": 0, "+토": 0, "-토": 0, "+금": 0, "-금": 0, "+수": 0, "-수": 0}
    for key in ("hour", "day", "month", "year"):
        s = pnorm[key]["stem"]
        b = pnorm[key]["branch"]
        s_el, s_yy = _STEM_EL_YY.get(s, ("", ""))
        b_el, b_yy = _BRANCH_EL_YY.get(b, ("", ""))
        if s_el and s_yy:
            yin_yang_counts[f"{s_yy}{s_el}"] += 1
        if b_el and b_yy:
            yin_yang_counts[f"{b_yy}{b_el}"] += 1
        hs = hidden.get(key) if isinstance(hidden.get(key), dict) else {}
        hlist = hs.get("hiddens") if isinstance(hs.get("hiddens"), list) else []
        hidden_out = []
        for h in hlist:
            if not isinstance(h, dict):
                continue
            st = str(h.get("stem") or "")
            hidden_out.append(
                {
                    "stem": st,
                    "role": str(h.get("role") or ""),
                    "sipsin": str(h.get("sipsin") or (ten_god_stem(day_stem, st) if day_stem and st else "")),
                }
            )
        pillars_out[key] = {
            "gan": s,
            "ji": b,
            "ganOhaeng": f"{s_yy}{s_el}" if s_el else "—",
            "jiOhaeng": f"{b_yy}{b_el}" if b_el else "—",
            "sipsin": ten_god_stem(day_stem, s) if day_stem and s else "—",
            "twelve": str((tf.get(key) or {}).get("fortune") or "—") if isinstance(tf.get(key), dict) else "—",
            "shinsal": by_where_shinsal.get(key, []),
            "hiddenStems": hidden_out,
        }

    oh = engine_result.get("oheng") if isinstance(engine_result.get("oheng"), dict) else {}
    counts = oh.get("counts") if isinstance(oh.get("counts"), dict) else {}
    total_counts = {
        "목": int(counts.get("목", counts.get("木", 0)) or 0),
        "화": int(counts.get("화", counts.get("火", 0)) or 0),
        "토": int(counts.get("토", counts.get("土", 0)) or 0),
        "금": int(counts.get("금", counts.get("金", 0)) or 0),
        "수": int(counts.get("수", counts.get("水", 0)) or 0),
    }

    km = analysis.get("kongmang")
    km_void = ()
    if isinstance(km, dict):
        vb = km.get("void_branches")
        if isinstance(vb, (list, tuple)) and len(vb) == 2:
            km_void = (str(vb[0]), str(vb[1]))

    daewoon = analysis.get("daewoon") if isinstance(analysis.get("daewoon"), list) else []
    dae_out = []
    for d in daewoon[:12]:
        if not isinstance(d, dict):
            continue
        dae_out.append(
            {
                "pillar": str(d.get("pillar") or ""),
                "startAge": d.get("start_age"),
                "endAge": d.get("end_age"),
                "direction": str(d.get("direction") or ""),
                "isCurrent": bool(d.get("is_current", False)),
            }
        )

    return {
        "pillars": pillars_out,
        "fiveElements": {"counts": total_counts, "yinYangCounts": yin_yang_counts},
        "gongmang": {
            "dayBase": _void_by_pillar(pnorm["day"]["stem"], pnorm["day"]["branch"]),
            "yearBase": _void_by_pillar(pnorm["year"]["stem"], pnorm["year"]["branch"]),
            "engineVoidBranches": list(km_void) if km_void else [],
        },
        "daewoon": dae_out,
        "calcMeta": {
            "monthTerm": str(((engine_result.get("pillars") or {}).get("meta") or {}).get("month_term") or ""),
            "monthTermTimeKst": str(((engine_result.get("pillars") or {}).get("meta") or {}).get("month_term_time_kst") or ""),
        },
    }


# -------------------------
# 입력/응답 스키마
# -------------------------
class AnalyzeRequest(BaseModel):
    name: str = Field(default="Unknown", description="사용자 이름")
    sex: str = Field(default="", description="남자/여자 등")
    birth: str = Field(..., description="YYYY-MM-DD HH:MM (예: 1990-01-01 09:30)")
    calendar: str = Field(
        default="solar",
        description="solar=날짜·시각을 양력 그대로 사용 | lunar / lunar_leap=날짜를 음력으로 보고 korean-lunar-calendar로 양력 변환 후 동일 시각 부착",
    )


class AnalyzeMetaResponse(BaseModel):
    ok: bool
    pdf_path: str
    created_at: str
    name: str
    sex: str
    birth: str


class CounselChatMessage(BaseModel):
    role: str = Field(..., description="user | assistant")
    text: str = ""


class CounselRequest(BaseModel):
    """프론트 BirthInputPayload + 대화 — 사주 엔진 요약을 매 요청마다 주입."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    name: str = ""
    date: str = Field(..., description="YYYY-MM-DD")
    time: str = Field(..., description="HH:MM")
    gender: str = Field(..., description="male | female")
    calendar: str = "solar"
    calendarApi: str = Field("solar", alias="calendarApi")
    lunarMonthKind: Optional[str] = Field(None, alias="lunarMonthKind")
    leapResolutionSource: Optional[str] = Field(None, alias="leapResolutionSource")
    messages: list[CounselChatMessage] = Field(default_factory=list)
    """후속 질문 문맥 — user/assistant 순서. 서버는 동일 생년월일로 엔진을 다시 계산해 요약을 만든다."""
    analysisSummary: Optional[str] = Field(
        None,
        alias="analysisSummary",
        description="클라이언트 캐시(디버그/확장용). 현재는 엔진 재계산 결과를 우선한다.",
    )

class CompatibilityPerson(BaseModel):
    date: str = Field(..., description="YYYY-MM-DD")
    time: str = Field(..., description="HH:MM")
    gender: str = Field(..., description="male | female")
    calendarApi: str = Field("solar", alias="calendarApi")


class CompatibilityRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    birth1: CompatibilityPerson
    birth2: CompatibilityPerson


class SoloLoveInsightRequest(BaseModel):
    """상대 사주 없이 본인 원국 기반 인연·썸 참고 문장."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    date: str = Field(..., description="YYYY-MM-DD")
    time: str = Field(..., description="HH:MM")
    gender: str = Field(..., description="male | female")
    calendarApi: str = Field("solar", alias="calendarApi")
    topic: str = Field(
        "general",
        description="general | sseom | timing | emotion",
    )


# -------------------------
# 유틸: 안전 변환
# -------------------------
def _to_dict(obj: Any) -> Any:
    """dataclass / dict / 기타를 최대한 dict로 바꿔준다."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj
    if is_dataclass(obj) and not isinstance(obj, type):
        try:
            return asdict(obj)
        except Exception:
            pass
    # dataclass 비슷한 객체(속성 접근) 방어
    if hasattr(obj, "__dict__"):
        try:
            return dict(obj.__dict__)
        except Exception:
            pass
    return obj


def _pillars_to_dict(pillars_obj: Any) -> Dict[str, Any]:
    """
    calculate_saju() 결과가 dataclass든 dict든 상관없이
    report_core.user_card가 기대하는 형태로 최대한 맞춘다:

    {
      "year": {"gan":"甲","ji":"子"},
      "month": {"gan":"乙","ji":"丑"},
      "day": {"gan":"丙","ji":"寅"},
      "hour": {"gan":"丁","ji":"卯"},
    }
    """
    p = _to_dict(pillars_obj)

    if isinstance(p, dict):
        # 이미 year/month/day/hour 구조면 그대로
        if all(k in p for k in ("year", "month", "day", "hour")):
            out: Dict[str, Any] = {}
            for k in ("year", "month", "day", "hour"):
                v = p.get(k)
                v = _to_dict(v)
                if isinstance(v, dict):
                    out[k] = {"gan": v.get("gan") or v.get("g") or "", "ji": v.get("ji") or v.get("j") or ""}
                else:
                    out[k] = {"gan": "", "ji": ""}
            return out

        # 다른 키로 들어온 경우(방어): 못 찾으면 빈 dict
        return {"year": {"gan": "", "ji": ""}, "month": {"gan": "", "ji": ""}, "day": {"gan": "", "ji": ""}, "hour": {"gan": "", "ji": ""}}

    # 속성 접근 fallback
    def _gj(getter: Any) -> Dict[str, str]:
        v = _to_dict(getter)
        if isinstance(v, dict):
            return {"gan": v.get("gan") or "", "ji": v.get("ji") or ""}
        return {"gan": "", "ji": ""}

    return {
        "year": _gj(getattr(pillars_obj, "year", None)),
        "month": _gj(getattr(pillars_obj, "month", None)),
        "day": _gj(getattr(pillars_obj, "day", None)),
        "hour": _gj(getattr(pillars_obj, "hour", None)),
    }


def _normalize_birth(birth: str, calendar: str = "solar") -> str:
    """
    birth를 'YYYY-MM-DD HH:MM'로 최대한 정규화.
    """
    s = (birth or "").strip()
    if "T" in s:
        s = s.replace("T", " ")
    if "+" in s:
        s = s.split("+", 1)[0]
    if s.endswith("Z"):
        s = s[:-1]
    s = s[:16].strip()
    # 형식 검증(실패하면 예외)
    try:
        datetime.strptime(s, "%Y-%m-%d %H:%M")
    except Exception:
        raise ValueError("birth format must be 'YYYY-MM-DD HH:MM'")

    cal = (calendar or "solar").strip().lower()
    if cal in ("lunar", "lunar_leap"):
        from engine.counsel_birth import normalize_birth_string

        d, t = s.split(" ", 1)
        return normalize_birth_string(d, t, cal)
    return s


def _inject_user_card(report: Dict[str, Any], *, name: str, sex: str, birth: str, pillars_obj: Any) -> None:
    """
    report_core.py 2페이지(사용자 요약 카드)가 비는 문제를 막기 위해
    report['user_card']를 확실히 채운다.
    """
    created = datetime.now().strftime("%Y-%m-%d")


    # solar는 화면에 그대로 보이게 문자열로 넣음(양력)
    solar_s = birth

    # lunar는 분석 결과에 있으면 최대한 끌어옴
    lunar_s = ""
    _br = report.get("birth_resolved")
    br: Dict[str, Any] = _br if isinstance(_br, dict) else {}
    lunar_obj = br.get("lunar") if isinstance(br.get("lunar"), dict) else None
    # lunar_obj가 dict면 YYYY-MM-DD(+윤달) 형태로 만들어서 user_card에 넣음
    if isinstance(lunar_obj, dict):
        y = lunar_obj.get("y") or lunar_obj.get("year")
        m = lunar_obj.get("m") or lunar_obj.get("month")
        d = lunar_obj.get("d") or lunar_obj.get("day")
        is_leap = bool(lunar_obj.get("is_leap") or lunar_obj.get("leap") or lunar_obj.get("isLeap"))
        try:
            if y and m and d:
                lunar_s = f"{int(y):04d}-{int(m):02d}-{int(d):02d}{' (윤달)' if is_leap else ''}"
        except Exception:
            lunar_s = ""

    report["user_card"] = {
        "name": name or "Unknown",
        "gender": sex or "",
        "solar": solar_s,
        "lunar": lunar_s,
        "pillars": _pillars_to_dict(pillars_obj),
        "meta": {"created_at_kst": created},
    }

    # 표지/기타에서도 이름/성별이 보이도록 profile도 보정
    _pf = report.get("profile")
    prof: Dict[str, Any] = dict(_pf) if isinstance(_pf, dict) else {}
    prof["name"] = name or prof.get("name") or "Unknown"
    prof["sex"] = sex or prof.get("sex") or ""
    report["profile"] = prof


# -------------------------
# FastAPI 앱
# -------------------------
app = FastAPI(title="Unteim API v1", version="1.0")


def _cors_allow_origins() -> list[str]:
    """쉼표 구분. 비어 있으면 `*` (개발 편의). 배포 시 `CORS_ORIGINS=https://app.example.com` 권장."""
    raw = (os.environ.get("CORS_ORIGINS") or "").strip()
    if not raw:
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


_origins = _cors_allow_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False if _origins == ["*"] else True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True, "service": "unteim-api"}


@app.get("/api/health")
def api_health():
    """프론트·로드밸런서용 — `/health`와 동일 응답."""
    return {"ok": True, "service": "unteim-api"}


@app.post("/api/counsel")
def counsel_chat(req: CounselRequest):
    """
    사주 엔진(analyze_full) → 상담용 요약 → OpenAI 채팅.
    후속 질문은 `messages`에 이전 user/assistant를 포함해 보내며, 서버는 매번 동일 생년월일로 엔진을 재실행해 요약을 프롬프트에 넣는다.
    """
    from engine.counsel_birth import birth_request_to_profile, normalize_birth_string

    d = req.model_dump(by_alias=True)
    cal_api = (d.get("calendarApi") or "solar").strip().lower()
    try:
        birth = normalize_birth_string(d["date"], d["time"], cal_api)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    profile = birth_request_to_profile(d)
    msgs = [{"role": m.role, "text": m.text} for m in req.messages]

    try:
        out = run_counsel_turn(birth_str=birth, profile=profile, chat_messages=msgs)
    except RuntimeError as e:
        msg = str(e)
        if msg == "LLM_NOT_CONFIGURED":
            raise HTTPException(
                status_code=503,
                detail="OPENAI_API_KEY가 설정되지 않아 AI 상담을 실행할 수 없습니다. 서버 환경 변수를 설정한 뒤 다시 시도해 주세요.",
            ) from e
        raise HTTPException(status_code=502, detail=msg) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"사주 엔진 또는 상담 처리 중 오류: {type(e).__name__}: {e}",
        ) from e

    return JSONResponse(content=out)


@app.post("/api/compatibility")
def compatibility(req: CompatibilityRequest):
    """사주 기반 궁합 분석."""
    from engine.counsel_birth import normalize_birth_string

    try:
        b1 = normalize_birth_string(req.birth1.date, req.birth1.time, req.birth1.calendarApi)
        b2 = normalize_birth_string(req.birth2.date, req.birth2.time, req.birth2.calendarApi)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    try:
        out = analyze_compatibility(
            birth1=b1,
            gender1=req.birth1.gender,
            birth2=b2,
            gender2=req.birth2.gender,
        )
        return JSONResponse(content=out)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"궁합 분석 중 오류: {type(e).__name__}: {e}",
        ) from e


@app.post("/api/solo-love-insight")
def solo_love_insight(req: SoloLoveInsightRequest):
    """상대 생년 없이 본인 사주만으로 인연·썸 흐름 참고 텍스트."""
    from engine.counsel_birth import normalize_birth_string

    try:
        birth = normalize_birth_string(req.date, req.time, req.calendarApi)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    try:
        out = build_solo_love_insight(birth, req.gender, req.topic)
        return JSONResponse(content=out)
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail=f"solo love insight failed: {type(e).__name__}: {e}\n{tb}",
        ) from e


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    """
    사주 분석 결과를 JSON으로 반환.
    PDF 생성 없이 빠르게 분석 결과만 받을 수 있다.
    """
    try:
        birth = _normalize_birth(req.birth, req.calendar)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        pillars = calculate_saju(birth)
        engine_result = analyze_full(cast(Any, pillars), birth_str=birth)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"engine failed: {type(e).__name__}: {e}",
        )

    from datetime import date as _date

    def _clean(obj):
        if obj is None:
            return None
        if isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, (datetime, _date)):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {str(k): _clean(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple, set)):
            return [_clean(v) for v in obj]
        if hasattr(obj, "__dict__"):
            return {k: _clean(v) for k, v in vars(obj).items() if not k.startswith("_")}
        return str(obj)

    result = _clean(engine_result)
    if isinstance(result, dict):
        result["saju_overview"] = _clean(_build_saju_overview(engine_result if isinstance(engine_result, dict) else {}))

    if isinstance(result, dict):
        result["request"] = {
            "name": req.name,
            "sex": req.sex,
            # 엔진·절기·대운에 쓰인 최종 생시(KST 문자열). calendar가 lunar/lunar_leap이면 음력→양력 변환 후 값.
            "birth": birth,
            "calendar": req.calendar,
        }

    return JSONResponse(content=result)


@app.post("/api/monthly-report", response_class=FileResponse)
def make_monthly_report(req: AnalyzeRequest):
    """
    ✅ 이 엔드포인트는 항상 out/monthly_report.pdf 하나만 만든다(덮어쓰기).
    그리고 PDF 파일을 바로 반환한다.
    """
    try:
        birth = _normalize_birth(req.birth, req.calendar)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    def _normalize_pillars(p: Any) -> Dict[str, Any]:
        """
        최종 형태:
        {"year":{"gan":"甲","ji":"子"}, "month":..., "day":..., "hour":...}
        """
        # 1) 이미 dict(정상 구조)
        if isinstance(p, dict) and isinstance(p.get("year"), dict):
            return p

        # 2) dataclass -> dict
        d = None
        try:
            if is_dataclass(p) and not isinstance(p, type):
                d = asdict(p)
        except Exception:
            d = None

        # 3) 일반 객체 -> __dict__
        if d is None:
            d = getattr(p, "__dict__", None)

        if not isinstance(d, dict):
            return {}

        out = {}
        for key in ("year", "month", "day", "hour"):
            item = d.get(key)
            if isinstance(item, dict):
                gan = item.get("gan") or item.get("stem") or item.get("g")
                ji  = item.get("ji")  or item.get("branch") or item.get("j")
            else:
                gan = getattr(item, "gan", None) or getattr(item, "stem", None)
                ji  = getattr(item, "ji", None)  or getattr(item, "branch", None)

            out[key] = {
                "gan": str(gan).strip() if gan else "",
                "ji":  str(ji).strip() if ji else "",
            }

        return out


    try:
        pillars = calculate_saju(birth)
        report = analyze_full(cast(Any, pillars), birth_str=birth)
        print(report.get("pillars"))
        print(report.get("analysis", {}).get("pillars"))

    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail=f"engine failed: {type(e).__name__}: {e}\n\n--- TRACEBACK ---\n{tb}",
        )

    if not isinstance(report, dict):
        raise HTTPException(status_code=500, detail="analyze_full returned non-dict report")

    # 2) user_card(2페이지 표) 채우기
    _inject_user_card(report, name=req.name, sex=req.sex, birth=birth, pillars_obj=pillars)

    # ---- A-1: 2페이지 카드가 비는 문제 방지 (동시 주입) ----
    _p = report.get("profile")
    profile: Dict[str, Any] = dict(_p) if isinstance(_p, dict) else {}
    profile["name"] = req.name or profile.get("name") or "Unknown"
    profile["sex"] = req.sex or profile.get("sex") or ""
    profile["birth_str"] = birth
    report["profile"] = profile

    _inp = report.get("input")
    inp: Dict[str, Any] = dict(_inp) if isinstance(_inp, dict) else {}
    inp["name"] = profile["name"]
    inp["sex"] = profile["sex"]
    inp["birth_str"] = birth
    report["input"] = inp

    br = report.get("birth_resolved") if isinstance(report.get("birth_resolved"), dict) else {}
    if not br:
        br = {"birth_str": birth}
    report["birth_resolved"] = br
    # ---------------------------------------------------------

    # 3) 출력 파일명 고정(덮어쓰기)
    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    out_path = str(OUT_PDF)

    try:
        build_monthly_report_pdf(report=report, out_path=out_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"pdf build failed: {type(e).__name__}: {e}")

    if not OUT_PDF.exists():
        raise HTTPException(status_code=500, detail="pdf not created")

    # 4) PDF 반환
    return FileResponse(
        path=out_path,
        media_type="application/pdf",
        filename="monthly_report.pdf",
    )


@app.post("/api/monthly-report/meta", response_model=AnalyzeMetaResponse)
def make_monthly_report_meta(req: AnalyzeRequest):
    """
    PDF를 만들되, 파일은 반환하지 않고 메타만 반환(디버깅/앱 연동용).
    """
    try:
        birth = _normalize_birth(req.birth, req.calendar)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        pillars = calculate_saju(birth)
        report = analyze_full(cast(Any, pillars), birth_str=birth)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"engine failed: {type(e).__name__}: {e}",
        ) from e


    if not isinstance(report, dict):
        raise HTTPException(status_code=500, detail="analyze_full returned non-dict report")

    _inject_user_card(report, name=req.name, sex=req.sex, birth=birth, pillars_obj=pillars)

    # ---- A-1: 2페이지 카드가 비는 문제 방지 (동시 주입) ----
    _p = report.get("profile")
    profile: Dict[str, Any] = dict(_p) if isinstance(_p, dict) else {}
    profile["name"] = req.name or profile.get("name") or "Unknown"
    profile["sex"] = req.sex or profile.get("sex") or ""
    profile["birth_str"] = birth
    report["profile"] = profile

    _inp = report.get("input")
    inp: Dict[str, Any] = dict(_inp) if isinstance(_inp, dict) else {}
    inp["name"] = profile["name"]
    inp["sex"] = profile["sex"]
    inp["birth_str"] = birth
    report["input"] = inp

    br = report.get("birth_resolved") if isinstance(report.get("birth_resolved"), dict) else {}
    if not br:
        br = {"birth_str": birth}
    report["birth_resolved"] = br
    # ---------------------------------------------------------

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    out_path = str(OUT_PDF)

    try:
        build_monthly_report_pdf(report=report, out_path=out_path)
    except Exception as e:
        print("=== ENGINE TRACEBACK (monthly-report/meta) ===")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"engine failed: {type(e).__name__}: {e}")


    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return AnalyzeMetaResponse(
        ok=True,
        pdf_path=out_path,
        created_at=created_at,
        name=req.name or "Unknown",
        sex=req.sex or "",
        birth=birth,
    )


# -------------------------
# 로컬 실행
# -------------------------
if __name__ == "__main__":
    import uvicorn  # type: ignore[import-untyped]

    host = os.environ.get("BACKEND_HOST", "127.0.0.1")
    port = int(os.environ.get("BACKEND_PORT", os.environ.get("PORT", "8000")))
    reload = os.environ.get("UVICORN_RELOAD", "1").strip().lower() in ("1", "true", "yes")

    uvicorn.run(
        "scripts.run_api_server_v1:app",
        host=host,
        port=port,
        reload=reload,
    )
