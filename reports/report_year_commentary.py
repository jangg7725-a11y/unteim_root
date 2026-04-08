# unteim/reports/report_year_commentary.py
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Dict

from reportlab.platypus import Paragraph, Spacer

from .report_styles_common import ensure_month_styles, bullets_block


def report_year_commentary(story, styles, report: Dict[str, Any]) -> None:
    """
    연간 섹션 PDF 출력 (표현만 담당)

    기대 데이터(권장):
      report['extra']['year_commentary'] = {
        'title': str,
        'summary': str,
        'bullets': list[str],
        'year': str|int (선택)
      }

    ⚠️ 아직 year_commentary가 없다면, 이 섹션은 조용히 건너뜀.
    """
    ensure_month_styles(styles)

    if not isinstance(report, dict):
        return

    extra = report.get("extra", {})
    if not isinstance(extra, dict):
        return

    # structured 연간 블록(엔진 calendar_year_fortune)이 있으면 중복 제목·요약을 피한다
    af = report.get("annual_fortune") or extra.get("annual_fortune")
    if isinstance(af, dict) and str(af.get("action_guide") or "").strip():
        return

    yc = extra.get("year_commentary")
    if not isinstance(yc, dict):
        return

    title = yc.get("title") or "연간 운세"
    summary = yc.get("summary") or ""
    bullets = yc.get("bullets") or []
    year = yc.get("year")

    header = str(title)
    if year:
        header = f"{header} ({year})"

    story.append(Paragraph(header, styles["MonthTitle"]))
    story.append(Spacer(1, 6))

    if summary:
        story.append(Paragraph(str(summary), styles["MonthBody"]))
        story.append(Spacer(1, 6))

    if isinstance(bullets, list) and bullets:
        blk = bullets_block([str(x) for x in bullets], styles, level=0)
        if blk:
            story.append(blk)
