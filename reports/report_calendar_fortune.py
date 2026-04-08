# reports/report_calendar_fortune.py
# -*- coding: utf-8 -*-
"""PDF: 연간 운세 + 양력 1~12월 월운 카드 (총운과 분리)."""
from __future__ import annotations

from typing import Any, Dict, List, Mapping

from reportlab.lib import colors
from reportlab.platypus import PageBreak, Paragraph, Spacer, KeepTogether

from reports.report_styles_common import build_counsel_card, ensure_report_fonts


def _font_name(styles: Mapping[str, Any]) -> str:
    for k in ("KBody", "KTitle", "Normal"):
        st = styles.get(k)
        if st and hasattr(st, "fontName"):
            return str(getattr(st, "fontName"))
    return "Helvetica"


def append_calendar_fortune_sections(story: List[Any], styles: Mapping[str, Any], report: Dict[str, Any]) -> None:
    """
    총운(기존 블록)과 별도로,
    연간 운세 → 1~12월 월운 순으로 story에 추가한다.
    """
    ensure_report_fonts()
    if not isinstance(report, dict):
        return

    af: Dict[str, Any]
    _af0 = report.get("annual_fortune")
    if isinstance(_af0, dict):
        af = _af0
    else:
        _ex = report.get("extra")
        _afx = _ex.get("annual_fortune") if isinstance(_ex, dict) else None
        af = _afx if isinstance(_afx, dict) else {}

    mrs = report.get("monthly_reports")
    if not isinstance(mrs, list) or not mrs:
        ex2 = report.get("extra")
        mrs = ex2.get("monthly_reports") if isinstance(ex2, dict) else []
    if not isinstance(mrs, list):
        mrs = []

    has_af = isinstance(af, dict) and str(af.get("core_flow") or "").strip()
    has_mrs = bool([x for x in mrs if isinstance(x, dict)])
    if not has_af and not has_mrs:
        return

    fn = _font_name(styles)
    h2 = styles.get("KTitle") or styles.get("KH2") or styles.get("KSection")
    body = styles.get("KBody") or styles.get("Normal")
    small = styles.get("KSmall") or body
    if h2 is None or body is None:
        return

    story.append(PageBreak())
    if has_af:
        story.append(Paragraph("<b><font color='#1565C0'>연간 운세</font></b>", h2))
        story.append(Spacer(1, 8))

    if has_af:
        af_block: Dict[str, Any] = af
        y = af_block.get("year", "")
        yp = af_block.get("year_pillar", "")
        head = f"{y}년 연간 운세" + (f" · 연간 {yp}" if yp else "")
        lines = [
            f"<b>올해의 핵심 흐름</b><br/>{af_block.get('core_flow', '')}",
            f"<b>직업·일</b><br/>{af_block.get('career', '')}",
            f"<b>재물</b><br/>{af_block.get('money', '')}",
            f"<b>인간관계</b><br/>{af_block.get('relationship', '')}",
            f"<b>건강</b><br/>{af_block.get('health', '')}",
            f"<b>올해 행동 가이드</b><br/>{af_block.get('action_guide', '')}",
        ]
        body_html = "<br/><br/>".join(lines)
        story.append(
            build_counsel_card(
                head,
                body_html,
                font_name=fn,
                paragraph_style=body,
                bg=colors.HexColor("#E8EAF6"),
                border_color=colors.HexColor("#3949AB"),
                border_w=1.5,
                pad=14,
                vpad=11,
            )
        )
        story.append(Spacer(1, 12))

    # --- 월별 1~12 ---
    rows: List[Dict[str, Any]] = [x for x in mrs if isinstance(x, dict)]
    rows.sort(key=lambda d: int(d.get("month", 0) or 0))

    if len(rows) < 1:
        return

    if has_af:
        story.append(Spacer(1, 4))

    ty = rows[0].get("year")
    if ty in (None, "") and has_af:
        ty = af.get("year")
    try:
        ty_s = str(int(ty)) if ty not in (None, "") else ""
    except Exception:
        ty_s = str(ty) if ty else ""

    story.append(Paragraph(f"<b><font color='#1565C0'>{ty_s + '년 ' if ty_s else ''}월별 운세 (1~12월)</font></b>", h2))
    story.append(
        Paragraph(
            "각 달은 양력 달력 기준 월간지·패턴 엔진 결과를 바탕으로, 직장·재물·관계·건강을 나누어 안내합니다.",
            small,
        )
    )
    story.append(Spacer(1, 10))

    for mr in rows:
        m = int(mr.get("month", 0) or 0)
        if m < 1 or m > 12:
            continue
        title = f"{m}월 · 월주 {mr.get('pillar') or mr.get('month_pillar') or '—'}"
        kw = str(mr.get("keywords") or "").strip()
        head_line = f"<b><font color='#283593'>{title}</font></b>"
        if kw:
            head_line += f"<br/><font size=9 color='#5C6BC0'>핵심 키워드: {kw}</font>"

        career = str(mr.get("career") or mr.get("job") or "").strip()
        tips = str(mr.get("tips") or mr.get("tip") or "").strip()
        parts = [
            f"<b>전체 흐름</b><br/>{mr.get('flow') or mr.get('summary') or ''}",
            f"<b>직장·일</b><br/>{career}",
            f"<b>재물</b><br/>{mr.get('money', '')}",
            f"<b>인연·관계</b><br/>{mr.get('relationship', '')}",
            f"<b>건강</b><br/>{mr.get('health', '')}",
            f"<b>주의 포인트</b><br/>{mr.get('caution', '')}",
            f"<b>활용 팁</b><br/>{tips}",
        ]
        body_html = "<br/><br/>".join(parts)

        card = build_counsel_card(
            head_line,
            body_html,
            font_name=fn,
            paragraph_style=body,
            bg=colors.HexColor("#FAFAFA"),
            border_color=colors.HexColor("#90A4AE"),
            border_w=1.2,
            pad=12,
            vpad=9,
        )

        story.append(KeepTogether([card, Spacer(1, 10)]))

        # 대략 1페이지에 1~2개월: 홀수 월 끝에서 페이지 나눔
        if m % 2 == 0 and m < 12:
            story.append(PageBreak())

    story.append(Spacer(1, 6))
