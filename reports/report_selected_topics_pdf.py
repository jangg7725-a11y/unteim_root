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
        fv = blk.get("free_version")
        pv = blk.get("premium_version")
        if isinstance(fv, dict) and isinstance(pv, dict):
            head = f"<b><font color='#6A1B9A'>{title}</font></b>"
            if status == "planned":
                head += "<br/><font size=9 color='#C62828'>[추가 예정 확장 분석]</font>"
            elif blk.get("tier") == "extend":
                head += "<br/><font size=9 color='#455A64'>[선택형 카테고리]</font>"

            free_lines: List[str] = []
            fs = str(fv.get("summary") or "").strip()
            if fs:
                free_lines.append(fs)
            fe = str(fv.get("emotion") or "").strip()
            if fe:
                free_lines.append("<font size=10>느낌(일부): " + fe + "</font>")
            free_body = "<br/><br/>".join(free_lines) if free_lines else "—"
            free_head = head + "<br/><font size=9 color='#1565C0'>[무료 · 요약]</font>"

            story.append(
                build_counsel_card(
                    free_head,
                    free_body,
                    font_name=fn,
                    paragraph_style=body,
                    bg=colors.HexColor("#E3F2FD"),
                    border_color=colors.HexColor("#64B5F6"),
                    border_w=1.2,
                    pad=12,
                    vpad=9,
                )
            )
            story.append(Spacer(1, 6))
            trig = str(blk.get("trigger_message") or "").strip()
            cta = str(blk.get("cta_message") or "").strip()
            if trig:
                story.append(
                    Paragraph(
                        f"<font size=10 color='#37474F'><i>{trig}</i></font>",
                        body,
                    )
                )
                story.append(Spacer(1, 4))
            if cta:
                story.append(
                    Paragraph(
                        f"<b><font size=10 color='#5D4037'>{cta}</font></b>",
                        body,
                    )
                )
            if trig or cta:
                story.append(Spacer(1, 8))
            else:
                story.append(Spacer(1, 6))

            prem_lines: List[str] = []
            for key, lab in (
                ("cause", "원인"),
                ("pattern", "반복"),
                ("emotion", "느낌(전체)"),
                ("insight", "이해"),
                ("action", "방향"),
            ):
                tx = pv.get(key)
                if isinstance(tx, str) and tx.strip():
                    prem_lines.append(f"<b>{lab}</b><br/>{tx.strip()}")
            nf = pv.get("narrative_flow")
            if isinstance(nf, str) and nf.strip():
                prem_lines.append("<b>흐름</b><br/>" + nf.strip())
            tp = pv.get("trauma_profile")
            if isinstance(tp, dict):
                labs = tp.get("labels") or []
                if isinstance(labs, list) and labs:
                    prem_lines.append(
                        "<font size=9>반복 패턴 성향: "
                        + " · ".join(str(x) for x in labs[:5])
                        + "</font>"
                    )
                tps = str(tp.get("summary") or "").strip()
                if tps:
                    prem_lines.append(tps)
            pbul = pv.get("bullets")
            if isinstance(pbul, list):
                for b in pbul[:12]:
                    if str(b).strip():
                        prem_lines.append(f"• {b}")
            prem_body = "<br/><br/>".join(prem_lines) if prem_lines else "—"
            prem_head = head + "<br/><font size=9 color='#E65100'>[유료 · 전체 리포트]</font>"

            story.append(
                build_counsel_card(
                    prem_head,
                    prem_body,
                    font_name=fn,
                    paragraph_style=body,
                    bg=colors.HexColor("#FFF8E1"),
                    border_color=colors.HexColor("#FFB300"),
                    border_w=1.6,
                    pad=12,
                    vpad=9,
                )
            )
            story.append(Spacer(1, 8))
            continue

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
        tp = blk.get("trauma_profile")
        if isinstance(tp, dict):
            labs = tp.get("labels") or []
            if isinstance(labs, list) and labs:
                lines.append("<font size=9>반복 패턴 성향: " + " · ".join(str(x) for x in labs[:5]) + "</font>")
            tps = str(tp.get("summary") or "").strip()
            if tps:
                lines.append(tps)
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
