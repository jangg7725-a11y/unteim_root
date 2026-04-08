# unteim/reports/monthly_report.py
# -*- coding: utf-8 -*-

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, List, Union

from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors

from .report_core import build_pdf_report  # ✅ report dict 그대로 PDF 생성
from engine.total_fortune_aggregator_v1 import enrich_report_with_total_fortune
from .report_styles_common import build_counsel_card, ensure_report_fonts

def _safe_get(report: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    path 예: "extra.month_commentary.title"
    """
    cur: Any = report
    for key in path.split("."):
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur

def _format_life_items(items: Any) -> List[str]:
    """
    평생운세/기타 리스트(dict)가 그대로 출력되는 것을 방지하고,
    사람이 읽는 문장 리스트로 변환한다.
    """
    if not isinstance(items, list):
        return []

    lines = []
    for it in items:
        if not isinstance(it, dict):
            continue
        name = str(it.get("name") or "").strip()
        where = str(it.get("where") or "").strip()
        branch = str(it.get("branch") or "").strip()
        detail = str(it.get("detail") or "").strip()

        # 필요한 필드만 조합 (빈값은 자동 제외)
        parts = [p for p in [name, f"({where})" if where else "", branch, detail] if p]
        if parts:
            lines.append(" · " + " ".join(parts))
    return lines


def _append_life_commentary_pretty(story: List[Any], styles: Mapping[str, Any], report: Dict[str, Any]) -> None:
    """
    report에서 평생운세(또는 life_commentary 계열)를 찾아
    dict 그대로 찍히지 않도록 안전하게 출력한다.
    """
    # 후보 키들(프로젝트마다 다를 수 있어서 안전망)
    extra = report.get("extra") or {}

    # 1) life_commentary가 dict면 그 안에 items가 있는지 확인
    life = report.get("life_commentary") or extra.get("life_commentary") or {}
    items = None

    if isinstance(life, dict):
        items = life.get("items") or life.get("lines")

    # 2) 혹시 report에 바로 리스트로 있는 경우도 대응
    if items is None:
        items = report.get("life_items") or extra.get("life_items")

    lines = _format_life_items(items)

    story.append(Paragraph("평생 운세", styles["KTitle"]))
    story.append(Spacer(1, 6))

    if not lines:
        story.append(Paragraph("평생 운세 데이터가 아직 준비되지 않았습니다.", styles["KBody"]))
        story.append(Spacer(1, 6))
        return

    for ln in lines[:12]:  # 너무 길면 페이지 밀림 방지 (상한 12줄)
        story.append(Paragraph(ln, styles["KBody"]))

def _pick_top3_month_patterns(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    extra.month_patterns 를 score 내림차순으로 정렬해서 Top3만 반환
    score 없으면 0으로 처리
    """
    extra = report.get("extra") or {}
    pats = extra.get("month_patterns") or []
    if not isinstance(pats, list):
        return []

    def _score(p: Any) -> float:
        try:
            return float((p or {}).get("score", 0.0) or 0.0)
        except Exception:
            return 0.0

    pats2 = [p for p in pats if isinstance(p, dict)]
    pats2.sort(key=_score, reverse=True)
    return pats2[:3]


def enrich_report_with_monthly_bundle(report: Dict[str, Any]) -> Dict[str, Any]:

    """
    report(dict)에 'monthly_bundle' 섹션을 추가해서
    PDF에 월간 리포트 섹션을 안정적으로 뿌릴 수 있게 만든다.
    """
    month_term = report.get("month_term") or _safe_get(report, "extra.month_term")
    month_term_time = report.get("month_term_time_kst") or _safe_get(report, "extra.month_term_time_kst")

    mc = _safe_get(report, "extra.month_commentary", {}) or {}
    title = mc.get("title", "월간 리포트")
    summary = mc.get("summary", "")
    bullets = mc.get("bullets", []) or []
    month_ganji = mc.get("month_ganji", "")

    report["monthly_bundle"] = {
        "month_term": month_term,
        "month_term_time_kst": month_term_time,
        "month_ganji": month_ganji,
        "title": title,
        "summary": summary,
        "bullets": bullets,
    }
    return report


def _tag_icon(tag: str) -> str:
    t = (tag or "").lower()
    if t in ("favorable", "good", "plus", "hojae"):
        return "▲"
    if t in ("caution", "bad", "minus", "yooeui"):
        return "▼"
    return "●"


def _box_style_for(tag: str) -> tuple[Any, Any]:
    t = (tag or "").lower()
    # 인쇄 가독성 우선: 너무 진한 색 피하고 “톤”만 구분
    if t in ("favorable", "good", "plus", "hojae"):
        return (colors.HexColor("#F3F8F3"), colors.HexColor("#1F5E2B"))  # bg, fg
    if t in ("caution", "bad", "minus", "yooeui"):
        return (colors.HexColor("#FFF3F3"), colors.HexColor("#7A1F1F"))
    return (colors.HexColor("#F5F5F5"), colors.HexColor("#333333"))


def _hex_color(c: Any) -> str:
    """
    reportlab color -> "#RRGGBB"
    """
    try:
        hv = c.hexval()  # "0xRRGGBB"
        if isinstance(hv, str) and hv.startswith("0x") and len(hv) == 8:
            return "#" + hv[2:]
    except Exception:
        pass
    return "#333333"


def _pick_font_name(styles: Mapping[str, Any]) -> str:
    """
    TableStyle용 기본 폰트 결정 (등록된 한글폰트가 있으면 그걸 쓰고,
    아니면 styles에서 뽑아오기)
    """
    for k in ("KBody", "KTitle", "Normal"):
        st = styles.get(k)
        if hasattr(st, "fontName") and isinstance(getattr(st, "fontName"), str):
            return getattr(st, "fontName")
    return "Helvetica"

def _append_samjae_box(story: List[Any], styles: Mapping[str, Any], report: Dict[str, Any]) -> None:
    """
    report["extra"]["total_fortune"]["samjae"] 를 PDF에 출력한다.
    """
    tf = (report.get("extra", {}) or {}).get("total_fortune", {}) or {}
    samjae = tf.get("samjae", {}) or {}

    story.append(Paragraph("삼재/복삼재 요약", styles["KTitle"]))
    story.append(Spacer(1, 6))

    if not isinstance(samjae, dict) or not samjae:
        story.append(Paragraph("삼재 정보가 없습니다.", styles["KBody"]))
        story.append(Spacer(1, 8))
        return

    is_samjae = samjae.get("is_samjae")
    phase = str(samjae.get("stage") or samjae.get("phase") or "-")
    mode = samjae.get("mode") or "NONE"
    risk_level = samjae.get("risk_level") if samjae.get("risk_level") is not None else samjae.get("riskLevel")
    relief = samjae.get("relief_score")
    risk = samjae.get("risk_score")
    group = samjae.get("group")

    mode_ko = {
        "NONE": "해당 없음",
        "NORMAL": "일반삼재",
        "MITIGATED": "완화삼재",
        "TRANSFORM": "전환삼재(복삼재)",
    }.get(mode, mode)

    is_samjae_ko = "예" if is_samjae is True else "아니오" if is_samjae is False else "-"

    rows = [
        ["삼재 해당", is_samjae_ko],
        ["대상", str(group) if group is not None else "-"],
        ["단계/국면", phase],
        ["구분", mode_ko],
        ["리스크 레벨(1~3)", str(risk_level) if risk_level is not None else "-"],
        ["완화 점수", str(relief) if relief is not None else "-"],
        ["리스크 점수", str(risk) if risk is not None else "-"],
    ]
    
    tbl = Table(rows, colWidths=["28%", "72%"], hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), _pick_font_name(styles)),
        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#cccccc")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.whitesmoke),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    story.append(tbl)
    story.append(Spacer(1, 10))

def _append_monthly_summary_box(story: List[Any], styles: Mapping[str, Any], title: str, lines: List[str]) -> None:
    """
    월간 핵심 요약 – 카테고리형 카드 출력
    """
    if not lines:
        return

    # title을 박스 상단 제목으로 쓰되, 내용은 lines를 그대로 출력
    data: List[List[Any]] = [[Paragraph(f"<b>{title}</b>", styles["KTitle"])]]

    category_icons = {
        "흐름": "◆",
        "판단": "◆",
        "관계": "◆",
        "재물": "◆",
        "일": "◆",
        "건강": "◆",
    }

    for line in lines:
        label = "요약"
        text = line.strip() if isinstance(line, str) else ""

        if isinstance(line, str) and ":" in line:
            a, b = line.split(":", 1)
            label = a.strip() or "요약"
            text = b.strip()

        icon = category_icons.get(label, "◆")
        content = f"<b>{icon} {label}</b>  {text}"
        data.append([Paragraph(content, styles["KBody"])])

    tbl = Table(data, colWidths=["100%"])
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F2F2F2")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#FAFAFA")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#DDDDDD")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E6E6E6")),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )

    story.append(tbl)
    story.append(Spacer(1, 14))


def _append_month_summary_boxes(story: List[Any], styles: Mapping[str, Any], mb: dict, report: dict) -> None:
    """
    mb: report.get("monthly_bundle") dict
    우선순위:
      1) monthly_scored / monthly_scored_items (dict list)
      2) monthly_highlights (dict)
      3) summary_lines fallback
    """
    items: List[Dict[str, str]] = []

    scored = mb.get("monthly_scored") or mb.get("monthly_scored_items") or []
    if isinstance(scored, list) and scored:
        for it in scored[:6]:
            if not isinstance(it, dict):
                continue
            tag = str(it.get("tag") or it.get("level") or "")
            label = str(it.get("label") or it.get("title") or "").strip()
            reason = str(it.get("reason") or it.get("summary") or it.get("text") or "").strip()
            if not label and not reason:
                continue
            items.append({"tag": tag, "label": label, "reason": reason})

    # highlights 대체
    if not items:
        hi = mb.get("monthly_highlights") or {}
        if isinstance(hi, dict):
            for tag in ("favorable", "caution"):
                arr = hi.get(tag) or []
                if isinstance(arr, list):
                    for s in arr[:3]:
                        if isinstance(s, str) and s.strip():
                            items.append({"tag": tag, "label": s.strip(), "reason": ""})

    # fallback: 요약 박스 1개는 항상 찍기
    if not items:
        title = str(mb.get("summary_title") or "이달의 핵심 요약")
        lines = mb.get("summary_lines") or [
            "판단과 선택의 정확도가 중요한 달입니다.",
            "무리한 확장보다 정리·조율이 흐름을 높입니다.",
            "약속/계약/말 한마디에 신중함이 필요합니다.",
        ]
        lines = [s for s in lines if isinstance(s, str) and s.strip()]
        _append_monthly_summary_box(story, styles, title=title, lines=lines)
        return

    story.append(Paragraph("월간 요약", styles["KTitle"]))
    story.append(Spacer(1, 6))

    font_name = _pick_font_name(styles)

    for it in items:
        tag = it.get("tag", "")
        icon = _tag_icon(tag)
        bg, fg = _box_style_for(tag)

        fg_hex = _hex_color(fg)

        label = (it.get("label") or "").strip()
        reason = (it.get("reason") or "").strip()

        left_html = f"<font color='{fg_hex}'><b>{icon} {label}</b></font>"
        right_html = f"<font color='{fg_hex}'>{reason}</font>" if reason else ""

        data = [[Paragraph(left_html, styles["KBody"]), Paragraph(right_html, styles["KBody"])]]
        tbl = Table(data, colWidths=["28%", "72%"], hAlign="LEFT")
        tbl.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), font_name),
                    ("BACKGROUND", (0, 0), (-1, -1), bg),
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#CCCCCC")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.0, colors.white),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(tbl)
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 8))
    # 삼재 박스는 report_monthly_bundle() 끝에서 한 번만 출력 (중복 방지)

def report_monthly_bundle(story: List[Any], styles: Union[Dict[str, ParagraphStyle], Mapping[str, Any]], report: Dict[str, Any]) -> None:
    """
    report_core.py에서 호출되는 월간 섹션 출력 함수
    """
    mb = report.get("monthly_bundle") or {}
    if not isinstance(mb, dict):
        return

    story.append(Paragraph("이달의 리포트", styles["KTitle"]))
    story.append(Spacer(1, 6))

    # ✅ 중복 방지: 월간 요약 박스는 한 번만
    if not report.get("__month_summary_drawn"):
        report["__month_summary_drawn"] = True
        _append_month_summary_boxes(story, styles, mb, report)

    # ✅ Top3는 요약과 독립적으로 항상 출력되게
    _append_top3_month_patterns_cards(story, styles, report, mb)
    # ✅ 삼재/복삼재 요약 박스 추가 (Top3 다음)
    _append_samjae_box(story, styles, report)

def _append_top3_month_patterns_cards(
    story: List[Any], styles: Mapping[str, Any], report: Dict[str, Any], mb: dict
) -> None:
    """
    extra.month_patterns에서 score 기준 Top3를 뽑아 카드형으로 출력
    """
    extra = report.get("extra") or {}
    if not isinstance(extra, dict):
        extra = {}

    raw_top3 = (
        extra.get("monthly_top3_cards")
        or extra.get("month_top3_cards")
        or extra.get("monthly_top3")
        or []
    )
    top3: List[Dict[str, Any]]
    if isinstance(raw_top3, list) and raw_top3:
        top3 = [x for x in raw_top3 if isinstance(x, dict)]
    else:
        top3 = []
    if not top3:
        raw = _pick_top3_month_patterns(report)
        conv: List[Dict[str, Any]] = []
        for p in raw:
            if not isinstance(p, dict):
                continue
            conv.append(
                {
                    "title": p.get("title") or p.get("id") or "포인트",
                    "summary": p.get("summary") or p.get("text") or "",
                    "signals": p.get("signals") or p.get("keywords") or [],
                    "tone": p.get("tone") or p.get("tag") or "neutral",
                    "level": p.get("level") or "",
                    "score": p.get("score", 0.0),
                    "is_main": False,
                }
            )
        top3 = conv

    if not top3:
        return


    story.append(PageBreak())
    story.append(Paragraph("이달의 TOP 3 포인트", styles["KTitle"]))
    story.append(Spacer(1, 6))

    font_name = _pick_font_name(styles)

    for p in top3:
        if not isinstance(p, dict):
            continue
        title = str(p.get("title") or p.get("id") or "").strip()
        tone = str(p.get("tone") or "").strip()  # good | neutral | caution
        level = str(p.get("level") or "").strip()
        score = p.get("score", 0.0)

        # 시그널(핵심 키워드)
        sigs = p.get("signals") or []
        if isinstance(sigs, list):
            sig_txt = ", ".join([str(x) for x in sigs if str(x).strip()][:4])
        else:
            sig_txt = ""

        summary = str(p.get("summary") or "").strip()
        
        is_main = bool(p.get("is_main"))

        # 톤에 따라 박스 색
        bg, fg = _box_style_for(tone)
        fg_hex = _hex_color(fg)

        head = f"<font color='{fg_hex}'><b>{title}</b></font>"
        meta = f"<font color='{fg_hex}'>({level}, score={score})</font>" if level else f"<font color='{fg_hex}'>(score={score})</font>"
        head_line = f"{head} {meta}"

        body_lines = []
        if sig_txt:
            body_lines.append(f"<b>키워드</b>: {sig_txt}")
        if summary:
            body_lines.append(summary)

        body_html = "<br/>".join(body_lines) if body_lines else "-"
        tbl = build_counsel_card(
            head_line,
            body_html,
            font_name=font_name,
            paragraph_style=styles["KBody"],
            bg=bg,
            border_w=2.0 if is_main else 1.2,
            pad=14 if is_main else 12,
            vpad=12 if is_main else 9,
        )
        story.append(tbl)
        story.append(Spacer(1, 8))

    story.append(Spacer(1, 6))

    # 월주(간지)
    month_ganji = mb.get("month_ganji")
    if isinstance(month_ganji, str) and month_ganji.strip():
        story.append(Paragraph(f"월주(간지): {month_ganji.strip()}", styles["KBody"]))
        story.append(Spacer(1, 4))


def _dict_str_any(x: Any) -> Dict[str, Any]:
    """Pyright/Pylance: nested dict를 Dict[str, Any]로 고정."""
    return x if isinstance(x, dict) else {}


def build_monthly_report_pdf(report: Dict[str, Any], out_path: str = "out/monthly_report.pdf") -> str:
    """
    ✅ 가장 중요한 원칙:
    - 엔진에서 만든 report(dict)를 절대 새로 만들지 않는다.
    - report를 그대로 build_pdf_report로 넘긴다. (pillars/analysis 유지)
    """
    if not isinstance(report, dict):
        raise ValueError("report must be dict")
    ensure_report_fonts()  # ✅ 한글/한자 폰트 깨짐 방지 (Table 포함)

    report = enrich_report_with_monthly_bundle(report)
    report = enrich_report_with_total_fortune(report)

    # -----------------------
    # 최소 키 보정 (표지/2페이지 안정)
    # -----------------------
    r: Dict[str, Any] = report
    profile = _dict_str_any(r.get("profile"))
    user_card = _dict_str_any(r.get("user_card"))
    meta = _dict_str_any(r.get("meta"))

    def _pick(*vals: object) -> str:
        for v in vals:
            if isinstance(v, str) and v.strip():
                return v.strip()
        return ""

    name = _pick(
        user_card.get("name"),
        profile.get("name"),
        r.get("name"),
        "Unknown",
    )
    sex = _pick(
        user_card.get("gender"),
        user_card.get("sex"),
        profile.get("sex"),
        r.get("sex"),
        "",
    )

    inp = _dict_str_any(r.get("input"))
    when = _dict_str_any(r.get("when"))
    base = _dict_str_any(r.get("base"))

    raw_birth = _pick(
        user_card.get("solar"),
        inp.get("birth_str"),
        inp.get("birth"),
        inp.get("dt_kst_iso"),
        r.get("birth_str"),
        r.get("birth"),
        profile.get("birth_str"),
        profile.get("birth"),
        when.get("birth_str"),
        when.get("birth"),
        base.get("birth_str"),
        base.get("birth"),
        r.get("dt_kst_iso"),
    )

    birth = raw_birth
    if isinstance(birth, str):
        if "T" in birth:
            birth = birth.replace("T", " ")
        if "+" in birth:
            birth = birth.split("+", 1)[0]
        if birth.endswith("Z"):
            birth = birth[:-1]
        birth = birth[:16].strip()

    if not birth:
        raise ValueError("birth_str missing in report (cannot build PDF)")

    # birth_resolved는 "없을 때만" input에서 가져오기 (있으면 건드리지 않음)
    if not isinstance(r.get("birth_resolved"), dict):
        br_raw = inp.get("birth_resolved")
        br_in = br_raw if isinstance(br_raw, dict) else None
        if br_in is not None:
            r["birth_resolved"] = br_in

    # meta.lunar_str 보장(있으면 표지/요약에 도움)
    lunar_str = _pick(
        user_card.get("lunar"),
        when.get("lunar_str"),
        when.get("lunar"),
        meta.get("lunar_str"),
        meta.get("lunar"),
    )
    if lunar_str:
        meta_out = dict(meta)
        meta_out["lunar_str"] = lunar_str
        r["meta"] = meta_out

    # report_core가 자주 보는 키들만 최소 보정
    r.setdefault("profile", {})
    if isinstance(r["profile"], dict):
        r["profile"].setdefault("name", name)
        r["profile"].setdefault("sex", sex)
        r["profile"].setdefault("birth", birth)

    r.setdefault("birth_str", birth)
    r.setdefault("name", name)
    r.setdefault("sex", sex)
    r.setdefault("meta", {})
    if isinstance(r["meta"], dict):
        r["meta"].setdefault("report_kind", "monthly")

    return build_pdf_report(report=r, out_path=out_path)


def build_month_commentary_payload_from_wolwoon(report: dict) -> dict:
    """
    WolWoonEngine 결과(혹은 report["wolwoon"])를
    report_month_commentary.py가 기대하는 mc 포맷으로 변환한다.
    """
    wol = report.get("wolwoon") or report.get("monthly_flow") or report.get("monthly_bundle") or []
    if not isinstance(wol, list) or not wol:
        return {}

    items = []
    for it in wol:
        if not isinstance(it, dict):
            continue
        label = it.get("label") or ""
        ganji = it.get("month_pillar") or it.get("month_ganji") or ""
        branch = it.get("month_branch") or ""

        bullets = []
        if branch:
            bullets.append(f"직장: {branch}월 흐름은 업무 방향을 정리하고 우선순위를 세우면 유리합니다.")
            bullets.append("재물: 지출 통제를 먼저 하고, 작은 고정비부터 정리해보세요.")
            bullets.append("건강: 수면/소화 루틴을 우선 점검하세요.")
        else:
            bullets.append("직장: 이번 달은 목표를 작게 잡고 실행력을 올리는 달입니다.")
            bullets.append("재물: 무리한 투자보다 현금흐름 안정이 우선입니다.")
            bullets.append("건강: 컨디션이 흔들리면 휴식부터 확보하세요.")

        items.append(
            {
                "title": f"{label} 월운",
                "summary": f"절기 기반 월운 요약(월주 {ganji})",
                "month_ganji": ganji,
                "bullets": bullets,
            }
        )

    return {"items": items}
