# unteim/reports/report_styles_common.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, ListFlowable, ListItem, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ----------------------------
# 1) Fonts
# ----------------------------

_FONT_DONE = False


def ensure_report_fonts() -> str:
    """
    ReportLab에 한글 폰트를 등록한다.
    - 반드시 PDF story(Paragraph/Table) 만들기 전에 1번은 호출되어야 함.
    - 성공 시 기본 한글 폰트명 반환 (예: "NotoSansKR")
    """
    global _FONT_DONE
    if _FONT_DONE:
        for n in ("NotoSansKR", "NotoSansKR-Regular"):
            if n in pdfmetrics.getRegisteredFontNames():
                return n
        return "Helvetica"

    root = Path(__file__).resolve().parents[2]  # unteim/reports -> 프로젝트 루트
    candidates = [
        root / "assets" / "fonts" / "NotoSansKR-Regular.ttf",
        root / "assets" / "fonts" / "NotoSansKR.ttf",
        root / "assets" / "fonts" / "NotoSansCJKkr-Regular.ttf",
        root / "assets" / "fonts" / "NotoSansCJKkr.ttf",
        root / "unteim" / "fonts" / "NotoSansKR-Regular.ttf",
        root / "fonts" / "NotoSansKR-Regular.ttf",
    ]

    font_path = None
    for p in candidates:
        if p.exists():
            font_path = p
            break

    if font_path is None:
        _FONT_DONE = True
        return "Helvetica"

    base_name = "NotoSansKR"
    if base_name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(base_name, str(font_path)))

    bold_path = font_path.parent / "NotoSansKR-Bold.ttf"
    if bold_path.exists() and f"{base_name}-Bold" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(f"{base_name}-Bold", str(bold_path)))

    _FONT_DONE = True
    return base_name


# ----------------------------
# 2) Cover styles
# ----------------------------

def add_cover_styles(styles):
    """
    styles가 StyleSheet(getSampleStyleSheet)일 수도 있고,
    dict일 수도 있으니 둘 다 지원.
    """
    base_font = ensure_report_fonts()

    def _get(key: str):
        try:
            return styles[key]
        except Exception:
            return styles.get(key) if isinstance(styles, dict) else None

    title_parent = _get("Title") or _get("KTitle") or _get("BodyText")
    body_parent = _get("BodyText") or _get("KBody") or title_parent

    cover_title = ParagraphStyle(
        name="CoverTitle",
        parent=title_parent,
        fontName=base_font,
        fontSize=26,
        leading=32,
        alignment=TA_CENTER,
        spaceAfter=10,
    )

    cover_sub = ParagraphStyle(
        name="CoverSubTitle",
        parent=body_parent,
        fontName=base_font,
        fontSize=13,
        leading=18,
        alignment=TA_CENTER,
        textColor=HexColor("#444444"),
        spaceAfter=4,
    )

    if hasattr(styles, "add"):
        # StyleSheet
        try:
            styles["CoverTitle"]
        except Exception:
            styles.add(cover_title)
        try:
            styles["CoverSubTitle"]
        except Exception:
            styles.add(cover_sub)
    else:
        # dict
        styles.setdefault("CoverTitle", cover_title)
        styles.setdefault("CoverSubTitle", cover_sub)

    return styles


# ----------------------------
# 3) Month styles
# ----------------------------

def ensure_month_styles(styles):
    """
    report_core에서 넘어오는 styles(dict)에 '월간 섹션 전용 스타일'만 추가한다.
    기존 키가 있으면 덮어쓰지 않는다(안전).
    """
    base_font = ensure_report_fonts()

    base_title = styles.get("KTitle") or styles.get("Title") or styles.get("Heading1")
    base_body = styles.get("KBody") or styles.get("BodyText") or styles.get("Normal")

    if "MonthTitle" not in styles:
        styles["MonthTitle"] = ParagraphStyle(
            name="MonthTitle",
            parent=base_title,
            fontName=base_font,
            fontSize=getattr(base_title, "fontSize", 16),
            leading=int(getattr(base_title, "leading", 20)),
            textColor=HexColor("#1F4E79"),
            spaceBefore=12,
            spaceAfter=10,
        )

    if "MonthSubHead" not in styles:
        styles["MonthSubHead"] = ParagraphStyle(
            name="MonthSubHead",
            parent=base_body,
            fontName=base_font,
            fontSize=max(12, int(getattr(base_body, "fontSize", 11) + 1)),
            leading=int(getattr(base_body, "leading", 15)),
            textColor=HexColor("#333333"),
            backColor=HexColor("#F3F5F7"),
            leftIndent=4,
            rightIndent=4,
            spaceBefore=10,
            spaceAfter=6,
            borderPadding=4,
        )

    if "MonthBody" not in styles:
        styles["MonthBody"] = ParagraphStyle(
            name="MonthBody",
            parent=base_body,
            fontName=base_font,
            fontSize=getattr(base_body, "fontSize", 11),
            leading=max(15, int(getattr(base_body, "leading", 15))),
            spaceBefore=2,
            spaceAfter=6,
        )

    if "MonthBullet" not in styles:
        styles["MonthBullet"] = ParagraphStyle(
            name="MonthBullet",
            parent=styles["MonthBody"],
            fontName=base_font,
            spaceBefore=0,
            spaceAfter=0,
        )

    return styles


def bullets_block(lines, styles, level=0):
    """
    lines: ['문장1', '문장2', ...]
    level: 0(기본) / 1(들여쓰기 더)
    """
    if not lines:
        return None

    left = 14 + (level * 10)
    bullet_indent = 6 + (level * 8)

    items = []
    for t in lines:
        if not t:
            continue
        items.append(ListItem(Paragraph(str(t), styles["MonthBullet"]), leftIndent=0))

    return ListFlowable(
        items,
        bulletType="bullet",
        leftIndent=left,
        bulletIndent=bullet_indent,
        bulletFontName=styles["MonthBullet"].fontName,
        bulletFontSize=9,
        bulletOffsetY=1,
        spaceBefore=2,
        spaceAfter=8,
    )


def split_month_bullets(bullets: list[str]):
    """
    월간 bullets를 직장 / 재물 / 건강으로 키워드 분류
    """
    job, money, health, etc = [], [], [], []

    for b in bullets:
        t = str(b)

        if any(k in t for k in ("직장", "업무", "상사", "동료", "이직", "승진", "일")):
            job.append(t)
        elif any(k in t for k in ("재물", "금전", "수입", "지출", "돈", "계약", "투자")):
            money.append(t)
        elif any(k in t for k in ("건강", "몸", "질병", "컨디션", "피로", "통증", "회복", "병원", "검진",
                                  "수면", "식사", "소화", "위", "장", "면역", "감기", "두통", "어지럼")):
            health.append(t)
        else:
            etc.append(t)

    return job, money, health, etc


# ----------------------------
# 4) Highlight box
# ----------------------------

COLOR_GOOD_BG = HexColor("#E8F5E9")   # 연한 초록
COLOR_GOOD_BR = HexColor("#43A047")  # 진한 초록
COLOR_WARN_BG = HexColor("#FFF3E0")   # 연한 주황
COLOR_WARN_BR = HexColor("#FB8C00")  # 진한 주황


def highlight_box(title: str, items: list[str], *, kind: str):
    if not items:
        return []

    if kind == "good":
        bg, br = COLOR_GOOD_BG, COLOR_GOOD_BR
    else:
        bg, br = COLOR_WARN_BG, COLOR_WARN_BR

    data = [[title]] + [[f"• {x}"] for x in items]

    tbl = Table(data, colWidths=["100%"])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 1.2, br),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, br),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return [tbl]


# ----------------------------
# 5) 상담 리포트 공통 카드 (TOP3 / 사주 핵심 요약 공용)
# ----------------------------

COUNSEL_CARD_BORDER = HexColor("#CCCCCC")
COUNSEL_CARD_INNER = HexColor("#E6E6E6")


def build_counsel_card(
    title_html: str,
    body_html: str = "",
    *,
    body_flowable: Any | None = None,
    font_name: str,
    paragraph_style: ParagraphStyle,
    bg: Any,
    col_width: str | float = "100%",
    border_color: Any | None = None,
    border_w: float = 1.2,
    pad: int = 12,
    vpad: int = 9,
    inner_grid: bool = True,
) -> Table:
    """
    월간 TOP3 카드와 동일한 박스 규칙: 제목 행 + 본문 행, BOX + INNERGRID, 넉넉한 패딩.
    grid 표가 아니라 '카드' 하나로 취급한다.
    body_flowable가 있으면 본문에 Paragraph 대신 해당 Flowable(Table 등)을 넣는다.
    """
    brd = border_color if border_color is not None else COUNSEL_CARD_BORDER
    head = Paragraph(title_html, paragraph_style)
    if body_flowable is not None:
        body = body_flowable
    else:
        body = Paragraph(body_html, paragraph_style)
    data = [[head], [body]]
    tbl = Table(data, colWidths=[col_width])
    ts = [
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), border_w, brd),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), pad),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad),
        ("TOPPADDING", (0, 0), (-1, -1), vpad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), vpad),
    ]
    if inner_grid:
        ts.append(("INNERGRID", (0, 0), (-1, -1), 0.4, COUNSEL_CARD_INNER))
    tbl.setStyle(TableStyle(ts))
    return tbl
