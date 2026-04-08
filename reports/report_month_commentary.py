# unteim/reports/report_month_commentary.py
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Dict

from reportlab.platypus import Paragraph, Spacer
from engine.month_narrative_basic import build_month_basic_narrative


# ✅ 공용 스타일/불릿 유틸(6단계)
from .report_styles_common import ensure_month_styles, bullets_block, split_month_bullets


def report_month_commentary(story, styles, report: Dict[str, Any]) -> None:
    """
    월간(주) 섹션 PDF 출력

    report['extra']['month_commentary'] dict 기대:
      {
        'title': str,
        'summary': str,
        'bullets': list[str],
        'month_ganji': str
      }
    """
    # 0) 월간 스타일(표현)만 보강
    ensure_month_styles(styles)

    # 1) 안전하게 month_commentary 꺼내기
    if not isinstance(report, dict):
        return

    extra = report.get("extra", {})
    if not isinstance(extra, dict):
        return

    mc = extra.get("month_commentary")
    if not isinstance(mc, dict):
        return

    title = mc.get("title") or "월간 운세"
    summary = mc.get("summary") or ""
    bullets = mc.get("bullets") or []
    month_ganji = mc.get("month_ganji") or ""
    # ✅ summary가 비어있으면: 패턴 엔진 없어도 동작하는 "기본형 월운 문장" 자동 생성
    if not summary:
        try:
            ysh = {}
            an = report.get("analysis") if isinstance(report.get("analysis"), dict) else {}
            if isinstance(an, dict) and isinstance(an.get("yongshin"), dict):
                ysh = an.get("yongshin") or {}
            nar = build_month_basic_narrative(
                birth_str=str(report.get("birth_str") or report.get("birth") or ""),
                when=str(report.get("when") or ""),
                oheng=report.get("oheng") if isinstance(report.get("oheng"), dict) else {},
                shinsal=(
                    report.get("shinsal_summary") if isinstance(report.get("shinsal_summary"), dict)
                    else (report.get("shinsal") if isinstance(report.get("shinsal"), dict) else {})
                ),
                wolwoon_top3=report.get("wolwoon_top3") or [],
                yongshin=ysh,
            )
            summary = nar.get("summary") or ""
            # ✅ bullets가 비어있다면: cautions/actions를 bullets에 붙여준다(기본형)
            if (not bullets) and (nar.get("cautions") or nar.get("actions")):
                bullets = []
                for c in (nar.get("cautions") or [])[:2]:
                    bullets.append(f"[주의] {c}")
                for a in (nar.get("actions") or [])[:2]:
                    bullets.append(f"[실행] {a}")
        except Exception:
            pass

    # 2) 월간 헤더 출력
    header = str(title)
    if month_ganji:
        header = f"{header} ({month_ganji})"

    story.append(Paragraph(header, styles["MonthTitle"]))
    story.append(Spacer(1, 6))

    # 3) 요약 출력
    if summary:
        story.append(Paragraph(str(summary), styles["MonthBody"]))
        story.append(Spacer(1, 6))
    # ✅ 월운 TOP3가 있을 때만 표시
    top3 = report.get("wolwoon_top3") or []
    if isinstance(top3, list) and len(top3) > 0:
        story.append(Paragraph("월운 TOP3", styles["MonthSubHead"]))
        for i, it in enumerate(top3[:3], start=1):
            if isinstance(it, dict):
                label = str(it.get("label") or it.get("name") or it.get("pattern") or "")
                score = it.get("score", "")
                line = f"- {i}위: {label}" if score in (None, "", 0) else f"- {i}위: {label} (점수 {score})"
            else:
                line = f"- {i}위: {str(it)}"
            story.append(Paragraph(line, styles["MonthBody"]))
        story.append(Spacer(1, 6))

    # 4) bullets 출력(직장/재물/건강 자동 분류)
    if isinstance(bullets, list) and bullets:
        job, money, health, etc = split_month_bullets([str(x) for x in bullets])

        if job:
            story.append(Paragraph("직장", styles["MonthSubHead"]))
            blk = bullets_block(job, styles, level=0)
            if blk:
                story.append(blk)

        if money:
            story.append(Paragraph("재물", styles["MonthSubHead"]))
            blk = bullets_block(money, styles, level=0)
            if blk:
                story.append(blk)

        if health:
            story.append(Paragraph("건강", styles["MonthSubHead"]))
            blk = bullets_block(health, styles, level=0)
            if blk:
                story.append(blk)

        # 분류 안 된 나머지(있으면 마지막에 출력)
        if etc:
            blk = bullets_block(etc, styles, level=0)
            if blk:
                story.append(blk)
