# unteim/reports/report_life_commentary.py
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Dict, List

from reportlab.platypus import Paragraph, Spacer


def _format_life_items(items: Any) -> List[str]:
    """
    평생운세가 dict/list/문자열 등 어떤 형태로 와도
    PDF에 'dict 그대로' 찍히지 않게 사람이 읽는 문장 리스트로 변환.
    """
    if items is None:
        return []

    # 1) 이미 문자열 리스트
    if isinstance(items, list) and all(isinstance(x, str) for x in items):
        return [("• " + x.strip()) for x in items if x and x.strip()]

    # 2) dict 리스트 (현재 사용자님 케이스)
    if isinstance(items, list):
        lines: List[str] = []
        for it in items:
            if not isinstance(it, dict):
                continue
            name = str(it.get("name") or "").strip()
            where = str(it.get("where") or "").strip()
            branch = str(it.get("branch") or "").strip()
            detail = str(it.get("detail") or "").strip()

            parts = []
            if name:
                parts.append(name)
            if where:
                parts.append(f"({where})")
            if branch:
                parts.append(branch)
            if detail:
                parts.append(detail)

            if parts:
                lines.append("• " + " ".join(parts))
        return lines

    # 3) dict 한 개
    if isinstance(items, dict):
        # 대표 키들 추출
        title = str(items.get("title") or "").strip()
        summary = str(items.get("summary") or "").strip()
        bullets = items.get("bullets") or items.get("lines") or []
        lines: List[str] = []
        if title:
            lines.append(f"• {title}")
        if summary:
            lines.append(f"• {summary}")
        if isinstance(bullets, list):
            for b in bullets:
                if isinstance(b, str) and b.strip():
                    lines.append("• " + b.strip())
        return lines

    # 4) 문자열 단독
    if isinstance(items, str) and items.strip():
        return ["• " + items.strip()]

    return []


def report_life_commentary(story, styles, report: Dict[str, Any]) -> None:
    """
    평생 섹션 PDF 출력.
    기대 데이터(권장):
      report['extra']['life_commentary'] = {title, summary, bullets[list[str]]}
    하지만 실제로는 list[dict] 등이 올 수 있으므로 안전 처리.
    """
    if not isinstance(report, dict):
        return

    extra = report.get("extra") or {}
    if not isinstance(extra, dict):
        extra = {}

    # 후보 키들(여러 버전 대응)
    lc = extra.get("life_commentary")
    title = "평생 운세"

    # dict 형태(권장)
    if isinstance(lc, dict):
        title = str(lc.get("title") or title).strip() or title
        items = lc.get("bullets") or lc.get("lines") or lc.get("items") or lc
    else:
        # list 형태(사용자님 현재 케이스) 또는 다른 위치
        items = (
            lc
            or report.get("life_commentary")
            or extra.get("life_items")
            or report.get("life_items")
        )

    lines = _format_life_items(items)

    story.append(Paragraph(title, styles["KTitle"]))
    story.append(Spacer(1, 6))

    if not lines:
        story.append(Paragraph("평생 운세 데이터가 아직 준비되지 않았습니다.", styles["KBody"]))
        story.append(Spacer(1, 6))
        return

    for ln in lines[:14]:  # 너무 길면 페이지 밀림 방지
        story.append(Paragraph(ln, styles["KBody"]))
    story.append(Spacer(1, 6))
