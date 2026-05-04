# -*- coding: utf-8 -*-
"""analyze_full 리포트 → 상담 LLM용 텍스트 요약 (intent별 섹션 순서 가변)."""

from __future__ import annotations

from typing import Any, Dict, List


def _clip(s: str, n: int = 2800) -> str:
    s = (s or "").strip()
    if len(s) <= n:
        return s
    return s[: n - 1] + "…"


# intent → 섹션 키 우선순위 (앞일수록 먼저 출력·강조)
SECTION_ORDER: Dict[str, List[str]] = {
    "personality": [
        "day_master",
        "oheng",
        "geukguk",
        "sipsin",
        "yongshin",
        "pillars",
        "flow",
        "domains",
        "monthly_engine",
        "shinsal",
        "unified",
    ],
    "wealth": [
        "yongshin",
        "sipsin",
        "domains",
        "oheng",
        "flow",
        "monthly_engine",
        "geukguk",
        "pillars",
        "day_master",
        "shinsal",
        "unified",
    ],
    "work": [
        "sipsin",
        "yongshin",
        "flow",
        "geukguk",
        "oheng",
        "pillars",
        "day_master",
        "domains",
        "monthly_engine",
        "shinsal",
        "unified",
    ],
    "relationship": [
        "sipsin",
        "shinsal",
        "yongshin",
        "flow",
        "geukguk",
        "pillars",
        "day_master",
        "oheng",
        "domains",
        "monthly_engine",
        "unified",
    ],
    "health": [
        "oheng",
        "domains",
        "yongshin",
        "flow",
        "sipsin",
        "pillars",
        "day_master",
        "geukguk",
        "monthly_engine",
        "shinsal",
        "unified",
    ],
    "exam": [
        "sipsin",
        "yongshin",
        "flow",
        "geukguk",
        "domains",
        "oheng",
        "pillars",
        "day_master",
        "monthly_engine",
        "shinsal",
        "unified",
    ],
    "general": [
        "pillars",
        "day_master",
        "oheng",
        "geukguk",
        "yongshin",
        "sipsin",
        "domains",
        "flow",
        "monthly_engine",
        "shinsal",
        "unified",
    ],
}


def _collect_sections(report: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, str]:
    """섹션 키 → 본문(제목 줄 포함). 비어 있으면 키 생략 가능."""
    sections: Dict[str, str] = {}

    lines_intro: List[str] = [
        f"- 프로필(참고): 이름={profile.get('name')}, 성별={profile.get('gender_label')}, "
        f"입력달력={profile.get('calendar_api')}"
    ]
    sections["_profile"] = "\n".join(lines_intro)

    pillars_obj = report.get("pillars")
    pillars: Dict[str, Any] = pillars_obj if isinstance(pillars_obj, dict) else {}
    plines: List[str] = ["[사주 원국]"]
    for key, label in (("year", "년"), ("month", "월"), ("day", "일"), ("hour", "시")):
        p = pillars.get(key) if isinstance(pillars, dict) else None
        if isinstance(p, dict):
            g, j = p.get("gan") or "", p.get("ji") or ""
            plines.append(f"- {label}주: {g}{j}")
    if len(plines) > 1:
        sections["pillars"] = "\n".join(plines)

    analysis_obj = report.get("analysis")
    a: Dict[str, Any] = analysis_obj if isinstance(analysis_obj, dict) else {}
    dm_obj = a.get("day_master")
    dm: Dict[str, Any] = dm_obj if isinstance(dm_obj, dict) else {}
    if dm:
        buf: List[str] = ["[일간·성향]"]
        for k in ("title", "summary", "headline", "text"):
            v = dm.get(k)
            if isinstance(v, str) and v.strip():
                buf.append(_clip(v, 1200))
                break
        sections["day_master"] = "\n".join(buf)

    oh_obj = a.get("oheng")
    oh: Dict[str, Any] = oh_obj if isinstance(oh_obj, dict) else {}
    if not oh and isinstance(report.get("oheng"), dict):
        oh = report["oheng"]
    if oh.get("counts"):
        sections["oheng"] = "[오행 분포]\n" + _clip(str(oh.get("counts")), 800)

    bs_obj = a.get("base_structure")
    bs: Dict[str, Any] = bs_obj if isinstance(bs_obj, dict) else {}
    gk_obj = bs.get("geukguk")
    gk: Dict[str, Any] = gk_obj if isinstance(gk_obj, dict) else {}
    if gk:
        sections["geukguk"] = "[격국]\n" + _clip(str(gk.get("label") or gk.get("name") or gk), 1200)

    ys_obj = a.get("yongshin")
    ys: Dict[str, Any] = ys_obj if isinstance(ys_obj, dict) else {}
    if ys:
        sections["yongshin"] = "[용신·희신·기신 축]\n" + _clip(str(ys), 3500)

    sp_obj = a.get("sipsin")
    sp: Dict[str, Any] = sp_obj if isinstance(sp_obj, dict) else {}
    if sp:
        buf = ["[십신 요약]"]
        summ_obj = sp.get("summary")
        summ: Dict[str, Any] = summ_obj if isinstance(summ_obj, dict) else {}
        if summ:
            buf.append(_clip(str(summ), 800))
        elif sp.get("profiles"):
            buf.append(_clip(str(sp.get("profiles")), 1500))
        sections["sipsin"] = "\n".join(buf)

    extra_obj = report.get("extra")
    extra: Dict[str, Any] = extra_obj if isinstance(extra_obj, dict) else {}
    dom_obj = extra.get("domains")
    dom: Dict[str, Any] = dom_obj if isinstance(dom_obj, dict) else {}
    if dom:
        sections["domains"] = "[재물·건강·문서 등 도메인 힌트]\n" + _clip(str(dom), 2500)

    fs_obj = report.get("flow_summary")
    fs: Dict[str, Any] = fs_obj if isinstance(fs_obj, dict) else {}
    if fs:
        flines: List[str] = ["[대운·세운·월운 해설 발췌]"]
        uv_obj = fs.get("ui_view")
        uv: Dict[str, Any] = uv_obj if isinstance(uv_obj, dict) else {}
        if uv:
            for fld in ("sewun_commentary", "wolwoon_commentary"):
                v = uv.get(fld)
                if v:
                    flines.append(_clip(str(v), 2000))
        dw_obj = fs.get("daewoon")
        dw: Dict[str, Any] = dw_obj if isinstance(dw_obj, dict) else {}
        notes = dw.get("notes")
        if notes:
            flines.append("[대운 해설]\n" + _clip(str(notes), 2000))
        if len(flines) > 1:
            sections["flow"] = "\n".join(flines)

    sh = report.get("shinsal")
    if sh is None:
        sh = a.get("shinsal")
    if sh:
        sections["shinsal"] = "[신살]\n" + _clip(str(sh), 2000)

    unified_obj = report.get("unified")
    u: Dict[str, Any] = unified_obj if isinstance(unified_obj, dict) else {}
    sm = u.get("summary")
    if sm:
        sections["unified"] = "[통합 요약]\n" + _clip(str(sm), 1500)

    # 월별 엔진(12개월) — 상담 시 월 흐름·행동 가이드 근거로 LLM에 전달
    mf_obj = report.get("monthly_fortune")
    mf: Dict[str, Any] = mf_obj if isinstance(mf_obj, dict) else {}
    months_raw = mf.get("months")
    if isinstance(months_raw, list) and months_raw:
        mlines: List[str] = [
            "[월별 운세 엔진 — AI 답변 시 아래 월별 문맥을 총운·대운과 함께 근거로 삼으세요. 없는 사실은 지어내지 말 것]"
        ]
        ys = str(mf.get("yearSummary") or "").strip()
        if ys:
            mlines.append(_clip(ys, 800))
        try:
            bm = int(mf.get("bestMonth") or 0)
            cm = int(mf.get("cautionMonth") or 0)
            if 1 <= bm <= 12 and 1 <= cm <= 12:
                mlines.append(f"(참고) 기회에 유리한 달: {bm}월 · 점검 권장 달: {cm}월")
        except Exception:
            pass
        for m in months_raw:
            if not isinstance(m, dict):
                continue
            try:
                mo = int(m.get("month") or 0)
            except Exception:
                continue
            if mo < 1 or mo > 12:
                continue
            parts: List[str] = []
            for key in (
                "oneLineConclusion",
                "mingliInterpretation",
                "realityChanges",
                "coreEvents",
                "opportunity",
                "riskPoints",
                "actionGuide",
                "behaviorGuide",
                "emotionCoaching",
                "narrative",
            ):
                v = m.get(key)
                if isinstance(v, str) and v.strip():
                    parts.append(_clip(v.strip(), 1100))
            if parts:
                mlines.append("")
                mlines.append(f"--- {mo}월 ---")
                mlines.extend(parts)
        blob = "\n".join(mlines).strip()
        if len(blob) > 80:
            sections["monthly_engine"] = _clip(blob, 9000)

    return sections


def summarize_report_for_counsel(
    report: Dict[str, Any],
    *,
    profile: Dict[str, Any],
    intent: str = "general",
) -> str:
    """
    intent에 따라 동일 데이터라도 섹션 출력 순서를 바꿔, LLM이 먼저 볼 블록을 조정한다.
    """
    intent_key = intent if intent in SECTION_ORDER else "general"
    sections = _collect_sections(report, profile)
    order = SECTION_ORDER[intent_key]

    out: List[str] = []
    out.append("【상담용 사주 분석 요약 — 아래 내용을 근거로 답하되, 과장·단정 금지】")
    prof = sections.pop("_profile", None)
    if prof:
        out.append(prof)

    seen: set[str] = set()
    for key in order:
        if key in sections and sections[key]:
            out.append("\n" + sections[key])
            seen.add(key)

    for key, body in sections.items():
        if key not in seen and body:
            out.append("\n" + body)

    return "\n".join(out).strip()
