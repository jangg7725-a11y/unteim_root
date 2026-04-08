# -*- coding: utf-8 -*-
"""
신살 리포트 PDF 생성 (완성본)
 - ReportLab 기반
 - shinsal_explainer 카드 + 지장간 섹션 포함
 - build_profile 미존재시 폴백 포함
"""

from __future__ import annotations

import os
import argparse
from typing import List, Dict, Any

# ===================== ReportLab =====================
from reportlab.lib import colors  # type: ignore
from reportlab.lib.pagesizes import A4  # type: ignore
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # type: ignore
from reportlab.lib.units import mm  # type: ignore
from reportlab.platypus import (  # type: ignore
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.pdfbase import pdfmetrics  # type: ignore
from reportlab.pdfbase.ttfonts import TTFont  # type: ignore
# === 폰트 등록 (NotoSansKR) ===
# 프로젝트 루트 기준 상대경로를 안전하게 계산
# ====== Korean font register (NotoSansKR) ======
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BASE_FONT = "NotoSansKR"
BASE_FONT_BOLD = "NotoSansKR-Bold"

def _find_font_file(candidates):
    for p in candidates:
        if Path(p).is_file():
            return str(p)
    return None

def register_korean_fonts():
    # 두 위치 모두 탐색: (1) 프로젝트 루트/fonts, (2) unteim/assets/fonts
    root = Path(__file__).resolve().parents[2]  # 프로젝트 루트 추정
    candidates_regular = [
        root / "fonts" / "NotoSansKR-Regular.ttf",
        root / "unteim" / "assets" / "fonts" / "NotoSansKR-Regular.ttf",
    ]
    candidates_bold = [
        root / "fonts" / "NotoSansKR-Bold.ttf",
        root / "unteim" / "assets" / "fonts" / "NotoSansKR-Bold.ttf",
    ]
    reg = _find_font_file(candidates_regular)
    bold = _find_font_file(candidates_bold)
    if reg:
        pdfmetrics.registerFont(TTFont(BASE_FONT, reg))
    if bold:
        pdfmetrics.registerFont(TTFont(BASE_FONT_BOLD, bold))
# === 폰트 등록 ===
pdfmetrics.registerFont(TTFont("NotoSansKR-Regular", "./fonts/NotoSansKR-Regular.ttf"))
pdfmetrics.registerFont(TTFont("NotoSansKR-Bold", "./fonts/NotoSansKR-Bold.ttf"))

# === 폰트 패밀리 등록 ===
pdfmetrics.registerFontFamily(
    "NotoSansKR",
    normal="NotoSansKR-Regular",
    bold="NotoSansKR-Bold",
    italic="NotoSansKR-Regular",   # Italic 없으니 Regular로 대체
    boldItalic="NotoSansKR-Bold"   # BoldItalic 없으니 Bold로 대체
)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(PROJECT_ROOT, "assets", "fonts")

FONT_REGULAR = os.path.join(FONT_DIR, "NotoSansKR-Regular.ttf")
FONT_BOLD    = os.path.join(FONT_DIR, "NotoSansKR-Bold.ttf")

if not os.path.exists(FONT_REGULAR) or not os.path.exists(FONT_BOLD):
    print("[WARN] 한글 폰트 파일을 찾지 못했습니다:",
          "\n  ", FONT_REGULAR,
          "\n  ", FONT_BOLD,
          "\nPDF에서 한글이 깨질 수 있어요. 경로/파일명을 확인하세요.")

try:
    pdfmetrics.registerFont(TTFont("NotoSansKR", FONT_REGULAR))
    pdfmetrics.registerFont(TTFont("NotoSansKR-Bold", FONT_BOLD))
except Exception as e:
    print("[WARN] 폰트 등록 실패:", e)

# ===================== 엔진 로직 =====================
from engine.shinsalDetector import detect_shinsal

from engine.shinsal_explainer import explain_shinsal_items, build_profile

# 지장간 유틸
from engine.hidden_stems import pillars_hidden_stems, count_stem_presence


# ===================== 폰트 등록 =====================
def _try_register_fonts() -> str:
    """
    NotoSansKR 가 있으면 등록하고 'NotoSansKR' 반환,
    없으면 기본 'Helvetica' 사용.
    """
    here = os.path.dirname(os.path.dirname(__file__))  # unteim/reports
    root = os.path.dirname(here)  # unteim
    font_dir = os.path.join(root, "assets", "fonts")
    reg = os.path.join(font_dir, "NotoSansKR-Regular.ttf")
    bold = os.path.join(font_dir, "NotoSansKR-Bold.ttf")

    try:
        if os.path.isfile(reg) and os.path.isfile(bold):
            pdfmetrics.registerFont(TTFont("NotoSansKR", reg))
            pdfmetrics.registerFont(TTFont("NotoSansKR-Bold", bold))
            return "NotoSansKR"
    except Exception:
        pass
    return "Helvetica"


# ===================== 스타일 =====================
def _build_styles(base_font: str):
    ss = getSampleStyleSheet()

    # 모든 기본 스타일의 폰트를 교체
    for k in list(ss.byName.keys()):
        st = ss.byName[k]
        st.fontName = base_font

    title = ParagraphStyle(
        "TitleK",
        parent=ss["Title"],
        fontName="NotoSansKR-Bold",   # 한글 제목은 Bold
        fontSize=20,
        leading=24,
        spaceAfter=8,
    )

    meta = ParagraphStyle(
        "MetaK",
        parent=ss["Normal"],
        fontName="NotoSansKR-Regular",   # 메타 정보는 Regular
        fontSize=10,
        leading=13,
        textColor=colors.grey,
        spaceAfter=6,
    )

    card_title = ParagraphStyle(
        "CardTitleK",
        parent=ss["Heading3"],
        fontName="NotoSansKR-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.black,
        spaceAfter=4,
    )

    bullets = ParagraphStyle(
        "BulletsK",
        parent=ss["Normal"],
        fontName="NotoSansKR-Regular",
        fontSize=11,
        leading=15,
        leftIndent=8,
        spaceAfter=4,
    )

    advice = ParagraphStyle(
        "AdviceK",
        parent=ss["Normal"],
        fontName="NotoSansKR-Regular",
        fontSize=11,
        leading=15,
        textColor=colors.darkblue,
        spaceAfter=6,
    )

    section = ParagraphStyle(
        "SectionK",
        parent=ss["Heading2"],
        fontName="NotoSansKR-Bold",
        fontSize=14,
        spaceBefore=8,
        spaceAfter=6,
    )

    table_header = ParagraphStyle(
        "TblHeadK",
        parent=ss["Normal"],
        fontName="NotoSansKR-Bold",
        fontSize=11,
        alignment=1,
    )

    return {
        "ss": ss,
        "title": title,
        "meta": meta,
        "card_title": card_title,
        "bullets": bullets,
        "advice": advice,
        "section": section,
        "table_header": table_header,
    }


# ===================== 카드 렌더 =====================
TONE_BG = {
    "positive": colors.HexColor("#F0FFF0"),  # 연녹
    "neutral": colors.whitesmoke,
    "caution": colors.HexColor("#FFF8E7"),  # 연살구
}
TONE_BD = {
    "positive": colors.HexColor("#7EC67E"),
    "neutral": colors.HexColor("#B0B0B0"),
    "caution": colors.HexColor("#E0A85C"),
}


def _card_table(card: Dict[str, Any], styles) -> Table:
    """
    카드 하나를 Table로 그린다.
    입력 예: {"title": "...", "bullets": [...], "advice": "...", "tone": "positive"}
    """
    title = card.get("title") or card.get("name") or "카드"
    bullets = card.get("bullets", [])
    advice = card.get("advice", "")
    tone = card.get("tone", "neutral")

    title_p = Paragraph(title, styles["card_title"])
    bullet_html = "<br/>".join([f"• {b}" for b in bullets])
    bullets_p = Paragraph(bullet_html, styles["bullets"])
    advice_p = Paragraph(f"※ {advice}" if advice else "", styles["advice"])

    data = [[title_p], [bullets_p], [advice_p]]
    t = Table(data, colWidths=[170 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), TONE_BG.get(tone, colors.whitesmoke)),
                ("BOX", (0, 0), (-1, -1), 0.7, TONE_BD.get(tone, colors.gray)),
                ("INNERPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return t


# ===================== 지장간 섹션 =====================
def _hidden_stems_section(pillars: Dict[str, Any], styles) -> List[Any]:
    """
    지장간 표 + 합계
    """
    story: List[Any] = []
    story.append(Spacer(1, 6))
    story.append(Paragraph("지장간 요약", styles["section"]))

    # 상세
    hs = pillars_hidden_stems(pillars)
    # 합계
    cnt = count_stem_presence(pillars)

    # 표 데이터
    header = ["기둥", "지장간(간: %)", ""]
    rows = [header]
    for k in ("year", "month", "day", "hour"):
        items = hs.get(k, [])
        items_txt = ", ".join([f"{g}:{p}%" for g, p in items]) if items else "-"
        rows.append([k, items_txt, ""])

    tbl = Table(rows, colWidths=[25 * mm, 120 * mm, 25 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFEFEF")),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.gray),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
                ("INNERPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(tbl)

    # 합계 문단
    sum_txt = " / ".join([f"{k}:{v}" for k, v in cnt.items()])
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"지장간 가중치 합계: {sum_txt}", styles["meta"]))
    return story


# ===================== 본문 구성 =====================
def build_story(
    title: str,
    meta_text: str,
    cards: List[Dict[str, Any]],
    pillars: Dict[str, Any],
    base_font: str,
) -> List[Any]:
    styles = _build_styles(base_font)
    story: List[Any] = []

    story.append(Paragraph(title, styles["title"]))
    story.append(Paragraph(meta_text, styles["meta"]))
    story.append(Spacer(1, 6))

    # 카드들
    for c in cards:
        story.append(_card_table(c, styles))
        story.append(Spacer(1, 4))

    # 지장간 섹션
    story += _hidden_stems_section(pillars, styles)

    # 페이지 끝
    story.append(PageBreak())
    return story


# ===================== 메인 =====================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="고객")
    ap.add_argument("--age", type=int, default=30)
    ap.add_argument("--sex", choices=["M", "F", "m", "f", "남", "여"], default="F")
    ap.add_argument("--job", default="service")
    ap.add_argument("--out", default="out/report.pdf")
    args = ap.parse_args()
    register_korean_fonts()

    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="고객")
    ap.add_argument("--age", type=int, default=30)
    ap.add_argument("--sex", choices=["M", "F", "m", "f", "남", "여"])
    ap.add_argument("--job", default="service")
    ap.add_argument("--out", default="out/report.pdf")
    args = ap.parse_args()
    
    # (데모) 기둥 샘플 — 실제 프로젝트에서는 엔진 연동하여 실제 값으로 대체
    pillars = {
        "year": ("丙", "午"),
        "month": ("庚", "子"),
        "day": ("戊", "申"),
        "hour": ("癸", "丑"),
    }

    # 신살 탐지 -> 카드화
    items = detect_shinsal(pillars)["items"]
    profile = build_profile(args.name, args.age, args.sex, args.job)
    cards = explain_shinsal_items(items, profile)

    # 제목/메타
    meta_text = f"{args.name} · {args.age}세 · {'여' if str(args.sex).upper()=='F' else '남'} · 직군:{args.job}"

    # 폰트 등록
    base_font = _try_register_fonts()

    # PDF 생성
    out_path = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    doc = SimpleDocTemplate(out_path, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm, topMargin=14 * mm, bottomMargin=14 * mm)
    story = build_story("신살 리포트", meta_text, cards, pillars, base_font)
    doc.build(story)

    print(f"[OK] PDF 저장: {out_path}")


if __name__ == "__main__":
    main()
