# engine/narrative/report_narrative.py
# -*- coding: utf-8 -*-
"""
사주 분석 결과(dict)로 narrative/*.json 키를 고르고,
2~3문장을 상담가 톤으로 이어 붙입니다. (GPT 없이 동작)
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional, Sequence

from utils.narrative_loader import get_list, get_sentence, load_sentences

# ---------------------------------------------------------------------------
# 안정적 난수 선택 (동일 입력 → 동일 문장)
# ---------------------------------------------------------------------------


def stable_pick(seed: str, options: Sequence[str]) -> str:
    opts = [x for x in options if isinstance(x, str) and x.strip()]
    if not opts:
        return ""
    h = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    idx = int(h[:8], 16) % len(opts)
    return opts[idx]


def compose_counselor_paragraph(parts: Sequence[str], *, max_parts: int = 3) -> str:
    """빈 문자열 제거 후 공백으로 이어 붙임 (한국어 상담 문단)."""
    out: List[str] = []
    for p in parts:
        s = (p or "").strip()
        if s and s not in out:
            out.append(s)
        if len(out) >= max_parts:
            break
    return " ".join(out)


# ---------------------------------------------------------------------------
# 키 생성: 오행·용신
# ---------------------------------------------------------------------------

_KR_TO_EN_FALLBACK = {"목": "wood", "화": "fire", "토": "earth", "금": "metal", "수": "water"}
_HANJA_ELEM = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}


def _norm_elem_kr(s: str) -> str:
    s = (s or "").strip()
    return _HANJA_ELEM.get(s, s)


def _element_en(kr: str) -> str:
    kr = _norm_elem_kr(kr)
    oh = load_sentences("oheng_sentences")
    m = oh.get("element_en") if isinstance(oh, dict) else None
    if isinstance(m, dict) and kr in m:
        return str(m[kr])
    return _KR_TO_EN_FALLBACK.get(kr, kr.lower() or "unknown")


def oheng_line_key_strength(kr: str, *, strong: bool) -> str:
    en = _element_en(kr)
    return f"{'strong' if strong else 'weak'}_{en}"


def yongsin_line_key_from_element(kr: str) -> str:
    kr = _norm_elem_kr(kr)
    if not kr:
        return "default"
    return f"yongsin_{_element_en(kr)}"


def extract_yongshin_element(yongshin_block: Any) -> str:
    if not isinstance(yongshin_block, dict):
        return ""
    el = yongshin_block.get("element")
    if el:
        return _norm_elem_kr(str(el).strip())
    inner = yongshin_block.get("yongshin")
    if isinstance(inner, dict) and inner.get("element"):
        return _norm_elem_kr(str(inner.get("element")).strip())
    return ""


# ---------------------------------------------------------------------------
# 월간 기본 내러티브 (month_narrative_basic 대체 본체)
# ---------------------------------------------------------------------------

_CAUTION_KEYWORDS = [
    "관재",
    "구설",
    "법",
    "분쟁",
    "사고",
    "부상",
    "수술",
    "교통",
    "손재",
    "지출",
    "파손",
    "분실",
    "시험",
    "합격",
    "승진",
    "평가",
    "이동",
    "이사",
    "변동",
    "출장",
    "이별",
    "이성",
    "연애",
    "인연",
]

_ACTION_KEYWORDS = [
    "시험",
    "합격",
    "자격증",
    "승진",
    "평가",
    "성과",
    "이동",
    "이사",
    "변동",
    "손재",
    "지출",
    "관재",
    "구설",
    "인연",
    "이성",
    "연애",
]


def _fmt_top3(top3: Any) -> List[Dict[str, Any]]:
    items = top3 if isinstance(top3, list) else ([] if not top3 else [top3])
    out: List[Dict[str, Any]] = []
    for i, it in enumerate(items[:3], start=1):
        if isinstance(it, dict):
            out.append(it)
        else:
            out.append({"rank": i, "label": str(it)})
    return out


def _safe_str(v: Any) -> str:
    return "" if v is None else str(v)


def _keyword_extras_from_monthly(
    label_text: str, *, branch: str
) -> List[str]:
    """branch: cautions | actions"""
    extras: List[str] = []
    keys = _CAUTION_KEYWORDS if branch == "cautions" else _ACTION_KEYWORDS
    prefix = f"monthly.{branch}"
    data = load_sentences("monthly_sentences")
    mroot = data.get("monthly") if isinstance(data, dict) else None
    if not isinstance(mroot, dict):
        return extras
    block = mroot.get(branch) if isinstance(mroot.get(branch), dict) else {}
    for kw in keys:
        if kw in label_text:
            k = f"keyword_{kw}"
            if isinstance(block, dict) and k in block and isinstance(block[k], str):
                extras.append(block[k])
    return extras


def build_month_basic_narrative(
    *,
    birth_str: str = "",
    when: str = "",
    oheng: Optional[Dict[str, Any]] = None,
    shinsal: Optional[Dict[str, Any]] = None,
    wolwoon_top3: Any = None,
    yongshin: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    narrative/*.json 기반 월간 문장 묶음.
    반환: summary(연속 2~3문장), cautions, actions, top3_lines,
          career/relationship/health (도메인별 1문장),
          narrative_debug (선택 키 요약, 선택)
    """
    oh = oheng or {}
    ss = shinsal or {}
    top3 = _fmt_top3(wolwoon_top3)

    seed = f"{birth_str}|{when}|{_safe_str(oh.get('dominant'))}|{_safe_str(oh.get('weak'))}"
    dominant = _safe_str(oh.get("dominant"))
    weak = _safe_str(oh.get("weak"))

    verdict = ""
    if isinstance(ss, dict):
        verdict = _safe_str(ss.get("verdict_label") or ss.get("verdict") or "")

    # --- 요약 후보 ---
    summary_parts: List[str] = []

    if dominant and weak:
        tpl = stable_pick(
            seed + "|summary_dom",
            get_list("monthly_sentences", "monthly.summary.dominant_weak", []),
        )
        try:
            summary_parts.append(tpl.format(dominant=dominant, weak=weak))
        except Exception:
            summary_parts.append(tpl)
    else:
        summary_parts.append(
            stable_pick(seed + "|summary_neutral", get_list("monthly_sentences", "monthly.summary.neutral", []))
        )

    # 오행 힌트 1문장 (강한 쪽 / 약한 쪽)
    if dominant:
        k1 = oheng_line_key_strength(dominant, strong=True)
        s1 = stable_pick(seed + "|oh_s", get_list("oheng_sentences", f"lines.{k1}", []))
        if s1:
            summary_parts.append(s1)
    if weak:
        k2 = oheng_line_key_strength(weak, strong=False)
        s2 = stable_pick(seed + "|oh_w", get_list("oheng_sentences", f"lines.{k2}", []))
        if s2:
            summary_parts.append(s2)

    ys_el = extract_yongshin_element(yongshin or {})
    if ys_el:
        yk = yongsin_line_key_from_element(ys_el)
        ys_line = stable_pick(seed + "|ys", get_list("yongsin_sentences", f"lines.{yk}", []))
        if not ys_line:
            ys_line = stable_pick(seed + "|ys_def", get_list("yongsin_sentences", "lines.default", []))
        if ys_line:
            summary_parts.append(ys_line)

    if verdict:
        vline = stable_pick(
            seed + "|verdict",
            get_list("monthly_sentences", "monthly.summary.verdict", []),
        )
        if vline:
            try:
                summary_parts.append(vline.format(verdict=verdict))
            except Exception:
                summary_parts.append(vline)

    # 기본 2~4문장(데이터에 따라): 베이스 + 오행(강/약) + 용신 + 판정
    summary = compose_counselor_paragraph(summary_parts, max_parts=4)

    # --- 주의 / 실행 ---
    label_text = " ".join([_safe_str(it.get("label")) for it in top3])

    cautions_pool: List[str] = _keyword_extras_from_monthly(label_text, branch="cautions") + get_list(
        "monthly_sentences", "monthly.cautions.pool", []
    )
    actions_pool: List[str] = _keyword_extras_from_monthly(label_text, branch="actions") + get_list(
        "monthly_sentences", "monthly.actions.pool", []
    )

    c1 = stable_pick(seed + "|c1", cautions_pool)
    c2 = stable_pick(seed + "|c2", [x for x in cautions_pool if x != c1])
    cautions = [c1]
    if c2:
        cautions.append(c2)

    a1 = stable_pick(seed + "|a1", actions_pool)
    a2 = stable_pick(seed + "|a2", [x for x in actions_pool if x != a1])
    actions = [a1]
    if a2:
        actions.append(a2)

    top3_lines: List[str] = []
    for it in top3:
        r = _safe_str(it.get("rank", ""))
        label = _safe_str(it.get("label", ""))
        score = it.get("score", None)
        if score is None or score == "":
            top3_lines.append(f"{r}위: {label}".strip())
        else:
            top3_lines.append(f"{r}위: {label} (점수 {score})".strip())

    career = stable_pick(seed + "|dom_c", get_list("monthly_sentences", "monthly.domains.career", []))
    relationship = stable_pick(seed + "|dom_r", get_list("monthly_sentences", "monthly.domains.relationship", []))
    health = stable_pick(seed + "|dom_h", get_list("monthly_sentences", "monthly.domains.health", []))

    return {
        "summary": summary,
        "cautions": cautions,
        "actions": actions,
        "top3_lines": top3_lines,
        "career": career,
        "relationship": relationship,
        "health": health,
        "narrative_keys": {
            "dominant": dominant,
            "weak": weak,
            "verdict": verdict,
            "yongshin_element": ys_el,
        },
    }


# ---------------------------------------------------------------------------
# full_analyzer: 연/일/평생 fallback 문장
# ---------------------------------------------------------------------------


def _pick_first_text(d: dict, keys: list[str]) -> str:
    for k in keys:
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def narrative_year_bundle(result: dict, when: dict) -> Dict[str, Any]:
    extra = result.get("extra") or {}
    analysis = result.get("analysis") or {}
    year = when.get("year") or when.get("year_solar") or when.get("y") or ""

    summary = ""
    if isinstance(extra, dict):
        summary = _pick_first_text(extra, ["year_summary", "annual_summary", "sewun_summary"])

    if not summary and isinstance(analysis, dict):
        oh = analysis.get("oheng")
        if isinstance(oh, dict):
            dom = _pick_first_text(oh, ["dominant", "dominant_element", "main_element"])
            weak = _pick_first_text(oh, ["weak", "lacking", "missing"])
            if dom or weak:
                tpl = get_sentence(
                    "monthly_sentences",
                    "year.fallback_summary_dom",
                    "올해 흐름은 '{dom}' 기세를 중심으로 움직이며, '{weak}' 보완이 관건입니다.",
                )
                try:
                    summary = tpl.format(dom=dom or "기본 균형", weak=weak or "생활 리듬")
                except Exception:
                    summary = tpl

    if not summary:
        summary = stable_pick(
            "year|fallback",
            get_list("monthly_sentences", "year.fallback_summary", ["올해는 큰 무리보다 기본을 지키는 쪽이 이득입니다."]),
        )

    bullets: list[str] = []
    if isinstance(extra, dict):
        b = extra.get("year_bullets") or extra.get("annual_bullets")
        if isinstance(b, list):
            bullets = [str(x) for x in b if isinstance(x, str) and x.strip()]

    if not bullets:
        mt = result.get("month_term")
        if isinstance(mt, list) and mt:
            bullets = [str(x) for x in mt[:3] if isinstance(x, str) and str(x).strip()]

    if not bullets:
        bullets = list(get_list("monthly_sentences", "year.fallback_bullets", []))

    title = "연간 운세" if not year else f"{year}년 운세"
    return {"title": title, "summary": summary, "bullets": bullets, "year": str(year) if year else ""}


def narrative_day_bundle(result: dict, when: dict) -> Optional[Dict[str, Any]]:
    extra = result.get("extra") or {}
    today = when.get("date") or when.get("today") or when.get("ymd") or ""

    summary = ""
    bullets: list[str] = []

    if isinstance(extra, dict):
        summary = _pick_first_text(extra, ["day_summary", "daily_summary"])
        b = extra.get("day_bullets") or extra.get("daily_bullets")
        if isinstance(b, list):
            bullets = [str(x) for x in b if isinstance(x, str) and x.strip()]

    if not summary or not bullets:
        mc = (extra.get("month_commentary") or {}) if isinstance(extra, dict) else {}
        if isinstance(mc, dict):
            if not summary:
                summary = _pick_first_text(mc, ["summary"]) or get_sentence(
                    "monthly_sentences", "day.fallback_summary", ""
                )
            if not bullets:
                mb = mc.get("bullets")
                if isinstance(mb, list) and mb:
                    bullets = [str(x) for x in mb[:2] if isinstance(x, str) and x.strip()]

    if not summary and not bullets:
        return None

    return {
        "title": "오늘의 운세",
        "summary": summary,
        "bullets": bullets,
        "date": str(today) if today else "",
    }


def narrative_life_bundle(result: dict) -> Dict[str, Any]:
    analysis = result.get("analysis") or {}
    extra = result.get("extra") or {}

    summary = ""
    bullets: list[str] = []

    if isinstance(extra, dict):
        summary = _pick_first_text(extra, ["life_summary", "lifetime_summary"])
        b = extra.get("life_bullets") or extra.get("lifetime_bullets")
        if isinstance(b, list):
            bullets = [str(x) for x in b if isinstance(x, str) and x.strip()]

    if not summary and isinstance(analysis, dict):
        oh = analysis.get("oheng")
        if isinstance(oh, dict):
            dom = _pick_first_text(oh, ["dominant", "dominant_element", "main_element"])
            weak = _pick_first_text(oh, ["weak", "lacking", "missing"])
            if dom or weak:
                tpl = get_sentence(
                    "monthly_sentences",
                    "life.fallback_summary_dom",
                    "전체적으로 '{dom}' 흐름이 인생의 선택을 이끌고, '{weak}' 보완이 운의 품질을 올립니다.",
                )
                try:
                    summary = tpl.format(dom=dom or "기본 기세", weak=weak or "균형")
                except Exception:
                    summary = tpl

    if not summary:
        summary = get_sentence("monthly_sentences", "life.fallback_summary", "")

    if not bullets and isinstance(analysis, dict):
        sh = analysis.get("shinsal")
        if isinstance(sh, dict):
            top = sh.get("top") or sh.get("highlights") or sh.get("items")
            if isinstance(top, list) and top:
                bullets = [str(x) for x in top[:4] if isinstance(x, str) and str(x).strip()]

    if not bullets:
        bullets = list(get_list("monthly_sentences", "life.fallback_bullets", []))

    return {"title": "평생 운세", "summary": summary, "bullets": bullets}
