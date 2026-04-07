# reports/report_selected_topics_pdf.py
# -*- coding: utf-8 -*-
"""선택형 주제 리포트 — 기본 리포트 후반에 구분하여 출력."""
from __future__ import annotations

from typing import Any, Dict, List, Mapping

from reportlab.lib import colors
from reportlab.platypus import PageBreak, Paragraph, Spacer

from reports.report_styles_common import build_counsel_card, ensure_report_fonts


def _font_name(styles: Mapping[str, Any]) -> str:
    for k in ("KBody", "KTitle", "Normal"):
        st = styles.get(k)
        if st and hasattr(st, "fontName"):
            return str(getattr(st, "fontName"))
    return "Helvetica"


def append_selected_topic_sections(story: List[Any], styles: Mapping[str, Any], report: Dict[str, Any]) -> None:
    """
    report['selected_reports'] 가 있을 때만 ‘선택형 주제’ 섹션을 추가한다.
    기본 리포트(총운·연간·월 등)와 시각적으로 구분한다.
    """
    ensure_report_fonts()
    if not isinstance(report, dict):
        return

    sr = report.get("selected_reports")
    if not isinstance(sr, dict) or not sr:
        ex = report.get("extra")
        if isinstance(ex, dict):
            sr = ex.get("selected_reports") or {}
    if not isinstance(sr, dict) or not sr:
        return

    _meta_raw = report.get("meta")
    meta: Dict[str, Any] = _meta_raw if isinstance(_meta_raw, dict) else {}
    order = meta.get("selected_report_keys")
    if not isinstance(order, list) or not order:
        order = meta.get("selected_topics")
    if not isinstance(order, list):
        order = []
    keys_order: List[str] = [str(x) for x in order if x in sr]
    for k in sr.keys():
        if k not in keys_order:
            keys_order.append(str(k))

    fn = _font_name(styles)
    h2 = styles.get("KTitle") or styles.get("KH2")
    body = styles.get("KBody") or styles.get("Normal")
    small = styles.get("KSmall") or body
    if h2 is None or body is None:
        return

    story.append(PageBreak())
    story.append(Paragraph("<b><font color='#4A148C'>선택형 주제 리포트</font></b>", h2))
    story.append(
        Paragraph(
            "아래는 요청하신 주제만 추가 생성된 확장 섹션입니다. "
            "기본 사주 요약·연간/월별 흐름과는 별도로 읽어 주세요.",
            small,
        )
    )
    story.append(Spacer(1, 10))

    for tid in keys_order:
        blk = sr.get(tid)
        if not isinstance(blk, dict):
            continue
        title = str(blk.get("title") or tid)
        status = blk.get("status")
        summary = str(blk.get("summary") or "").strip()
        bullets = blk.get("bullets") or []
        if not isinstance(bullets, list):
            bullets = []

        head = f"<b><font color='#6A1B9A'>{title}</font></b>"
        if status == "planned":
            head += "<br/><font size=9 color='#C62828'>[추가 예정 확장 분석]</font>"
        elif blk.get("tier") == "extend":
            head += "<br/><font size=9 color='#455A64'>[선택형 카테고리]</font>"

        lines = []
        if summary:
            lines.append(summary)
        for b in bullets[:10]:
            if str(b).strip():
                lines.append(f"• {b}")
        body_html = "<br/><br/>".join(lines) if lines else "—"

        bg = colors.HexColor("#F3E5F5") if status == "planned" else colors.HexColor("#FAFAFA")
        border = colors.HexColor("#CE93D8") if status == "planned" else colors.HexColor("#B39DDB")

        story.append(
            build_counsel_card(
                head,
                body_html,
                font_name=fn,
                paragraph_style=body,
                bg=bg,
                border_color=border,
                border_w=1.4,
                pad=12,
                vpad=9,
            )
        )
        story.append(Spacer(1, 8))

    story.append(Spacer(1, 6))
