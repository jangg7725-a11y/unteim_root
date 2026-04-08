# unteim/reports/report_day_commentary.py
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Dict

from reportlab.platypus import Paragraph, Spacer

from .report_styles_common import ensure_month_styles, bullets_block


def report_day_commentary(story, styles, report: Dict[str, Any]) -> None:
    """
    일간 섹션 PDF 출력 (표현만 담당)

    기대 데이터(권장):
      report['extra']['day_commentary'] = {
        'title': str,
        'summary': str,
        'bullets': list[str],
        'date': str (선택)  # 'YYYY-MM-DD'
      }

    ⚠️ 아직 day_commentary가 없다면, 이 섹션은 조용히 건너뜀.
    """
    ensure_month_styles(styles)

    if not isinstance(report, dict):
        return

    extra = report.get("extra", {})
    if not isinstance(extra, dict):
        return

    dc = extra.get("day_commentary")
    if not isinstance(dc, dict):
        return

    title = dc.get("title") or "오늘의 운세"
    summary = dc.get("summary") or ""
    bullets = dc.get("bullets") or []
    date = dc.get("date")

    header = str(title)
    if date:
        header = f"{header} ({date})"

    story.append(Paragraph(header, styles["MonthTitle"]))
    story.append(Spacer(1, 6))

    if summary:
        story.append(Paragraph(str(summary), styles["MonthBody"]))
        story.append(Spacer(1, 6))

    if isinstance(bullets, list) and bullets:
        blk = bullets_block([str(x) for x in bullets], styles, level=0)
        if blk:
            story.append(blk)
