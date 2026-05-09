# reports/report_core.py
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Dict, Optional
from pathlib import Path
from datetime import date, datetime, time

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from zoneinfo import ZoneInfo

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    HRFlowable,
    ListFlowable,
    ListItem,
    Table,
    TableStyle,
)

from reports.report_styles_common import add_cover_styles, ensure_month_styles


# ✅ 같은 패키지(reports) 모듈 — 절대 import (Pylance/루트 구조 호환)
try:
    from reports.report_month_commentary import report_month_commentary
except Exception:
    report_month_commentary = None  # type: ignore

try:
    from reports.monthly_report import report_monthly_bundle
except Exception:
    report_monthly_bundle = None  # type: ignore

try:
    from reports.report_year_commentary import report_year_commentary
except Exception:
    report_year_commentary = None  # type: ignore

try:
    from reports.report_day_commentary import report_day_commentary
except Exception:
    report_day_commentary = None  # type: ignore

try:
    from reports.report_life_commentary import report_life_commentary
except Exception:
    report_life_commentary = None  # type: ignore

try:
    from reports.report_calendar_fortune import append_calendar_fortune_sections
except Exception:
    append_calendar_fortune_sections = None  # type: ignore

try:
    from reports.report_selected_topics_pdf import append_selected_topic_sections
except Exception:
    append_selected_topic_sections = None  # type: ignore

def _pick_str(*vals: object) -> str:
    for v in vals:
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""

def _calc_lunar_from_birth(birth: str) -> dict | None:
    """
    birth: 'YYYY-MM-DD HH:MM' (양력 입력 가정)
    return: {'y': int, 'm': int, 'd': int, 'is_leap': bool} or None
    """
    from datetime import datetime

    def _as_int(x):
        try:
            if x is None:
                return None
            return int(x)
        except Exception:
            return None

    def _normalize_out(out):
        # dict 형태
        if isinstance(out, dict):
            # 1) date 문자열이 있으면 우선 파싱 (예: "1989-12-05")
            date_s = out.get("date") or out.get("lunar_date") or out.get("lunarDate") or out.get("ymd")
            if isinstance(date_s, str) and date_s.strip():
                try:
                    yy, mm, dd = date_s.strip().split("-")
                    y = _as_int(yy); m = _as_int(mm); d = _as_int(dd)
                    if y is None or m is None or d is None:
                        return None
                    is_leap = bool(
                        out.get("is_leap") or out.get("isLeap") or out.get("leap")
                        or out.get("leap_month") or out.get("is_leap_month")
                        or out.get("is_intercalation") or out.get("isIntercalation")
                    )
                    return {"y": y, "m": m, "d": d, "is_leap": is_leap}
                except Exception:
                    pass

            # 2) y/m/d 키 계열
            y = _as_int(out.get("y") or out.get("ly") or out.get("year"))
            m = _as_int(out.get("m") or out.get("lm") or out.get("month"))
            d = _as_int(out.get("d") or out.get("ld") or out.get("day"))
            if y is None or m is None or d is None:
                return None

            is_leap = bool(
                out.get("is_leap") or out.get("isLeap") or out.get("leap")
                or out.get("leap_month") or out.get("is_leap_month")
                or out.get("is_intercalation") or out.get("isIntercalation")
            )
            return {"y": y, "m": m, "d": d, "is_leap": is_leap}

        # tuple/list 형태: (y,m,d,is_leap?) or (y,m,d)
        if isinstance(out, (tuple, list)) and len(out) >= 3:
            y = _as_int(out[0]); m = _as_int(out[1]); d = _as_int(out[2])
            if y is None or m is None or d is None:
                return None
            is_leap = bool(out[3]) if len(out) >= 4 else False
            return {"y": y, "m": m, "d": d, "is_leap": is_leap}

        return None

    # birth 파싱
    try:
        dt = datetime.strptime(birth.strip(), "%Y-%m-%d %H:%M")
    except Exception:
        return None

    out = None

    # ✅ 1) lunar_kr 우선 (정확도 우선)
    try:
        from engine.lunar_kr import solar_to_lunar as to_lunar_kr  # type: ignore
        try:
            out = to_lunar_kr(dt)
        except Exception:
            out = None

        if out is None:
            try:
                out = to_lunar_kr(dt.date())
            except Exception:
                out = None
    except Exception:
        out = None

    # ✅ 2) lunar_converter fallback (lunar_kr 실패 시)
    if out is None:
        try:
            from engine.lunar_converter import to_lunar  # type: ignore
            try:
                out = to_lunar(dt)
            except Exception:
                out = None

            if out is None:
                try:
                    out = to_lunar(datetime.combine(dt.date(), time.min))
                except Exception:
                    out = None
        except Exception:
            out = None

    if out is None:
        return None

    return _normalize_out(out)



# -----------------------------
# 2) 표지(고정 레이아웃)
# -----------------------------
def _append_cover_page(story, styles, *, title: str, subtitle_lines: list[str]):
    add_cover_styles(styles)

    TOP_SPACE = 55 * mm
    TITLE_GAP = 6 * mm
    SUB_LINE_GAP = 2 * mm
    BLOCK_GAP = 12 * mm
    LINE_GAP = 6 * mm
    FOOTER_GAP = 55 * mm

    story.append(Spacer(1, TOP_SPACE))

    gen_date = date.today().strftime("%Y-%m-%d")
    date_table = Table([[f"생성일자 {gen_date}"]], colWidths=[160], rowHeights=[14])
    date_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.grey),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(date_table)

    story.append(Paragraph(str(title), styles["CoverTitle"]))
    story.append(Spacer(1, TITLE_GAP))

    for line in (subtitle_lines or []):
        if isinstance(line, str) and line.strip():
            story.append(Paragraph(line.strip(), styles["CoverSubTitle"]))
            story.append(Spacer(1, SUB_LINE_GAP))

    story.append(Spacer(1, BLOCK_GAP))
    story.append(HRFlowable(width="68%", thickness=1, lineCap="round"))
    story.append(Spacer(1, LINE_GAP))

    story.append(Spacer(1, FOOTER_GAP))
    story.append(Paragraph("UNTEIM REPORT", styles["CoverSubTitle"]))


# -----------------------------
# 3) 월간 요약 박스(표지 다음 페이지 1회)
# -----------------------------
def _append_monthly_summary_box_titled(story, styles, *, title: str, lines: list[str]) -> None:
    lines = [s for s in lines if isinstance(s, str) and s.strip()]
    if not lines:
        return

    box_data = [[Paragraph(f"<b>{title}</b>", styles["KTitle"])]]
    for line in lines:
        box_data.append([Paragraph(line, styles["KBody"])])

    table = Table(box_data, colWidths=[170 * mm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
                ("BOX", (0, 0), (-1, -1), 1, colors.lightgrey),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    story.append(Spacer(1, 6 * mm))
    story.append(table)
    story.append(Spacer(1, 10 * mm))

def _append_oheng_section(story, styles, report: dict) -> None:
    """오행 분포를 PDF에 출력"""
    oheng = None
    if isinstance(report, dict):
        oheng = report.get("oheng")
        if not oheng:
            oheng = (report.get("analysis") or {}).get("oheng")

    if not isinstance(oheng, dict):
        return

    counts = oheng.get("counts")
    if not isinstance(counts, dict) or not counts:
        return

    story.append(Paragraph("오행 분포", styles.get("KTitle") or next(iter(styles.values()))))
    story.append(Spacer(1, 6))

    rows = [["오행", "개수", "비율"]]
    total = sum(int(v) for v in counts.values() if isinstance(v, (int, float)))
    if total == 0:
        total = 1

    for elem in ["木", "火", "土", "金", "水"]:
        cnt = int(counts.get(elem, 0))
        pct = f"{cnt / total * 100:.0f}%"
        rows.append([elem, str(cnt), pct])

    font_name = "NotoSansKR"
    for k in ("KBody", "KTitle"):
        st = styles.get(k)
        if st and hasattr(st, "fontName"):
            font_name = st.fontName
            break

    tbl = Table(rows, colWidths=["30%", "35%", "35%"], hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EAF6")),
        ("BACKGROUND", (0, 1), (0, -1), colors.whitesmoke),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#cccccc")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.whitesmoke),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 6))

    summary = oheng.get("summary")
    if isinstance(summary, str) and summary.strip():
        story.append(Paragraph(f"요약: {summary}", styles.get("KBody") or next(iter(styles.values()))))
        story.append(Spacer(1, 4))

    tips = oheng.get("tips")
    if isinstance(tips, list):
        for tip in tips:
            if isinstance(tip, str) and tip.strip():
                story.append(Paragraph(f"• {tip}", styles.get("KBody") or next(iter(styles.values()))))
    story.append(Spacer(1, 12))


def _append_shinsal_section(story, styles, report: dict) -> None:
    """신살 요약을 PDF에 출력"""
    shinsal = None
    if isinstance(report, dict):
        shinsal = report.get("shinsal")
        if not shinsal:
            shinsal = (report.get("analysis") or {}).get("shinsal")

    if not isinstance(shinsal, dict):
        return

    if "error" in shinsal:
        return

    items = shinsal.get("items")
    if not isinstance(items, list) or not items:
        return

    story.append(Paragraph("신살 분석", styles.get("KTitle") or next(iter(styles.values()))))
    story.append(Spacer(1, 6))

    summary = shinsal.get("summary", {})
    if isinstance(summary, dict):
        verdict = summary.get("verdict", "")
        total = summary.get("total", 0)
        good = summary.get("good_total", 0)
        bad = summary.get("bad_total", 0)
        if verdict:
            story.append(Paragraph(
                f"종합 판정: {verdict} (총 {total}건 / 길 {good} · 흉 {bad})",
                styles.get("KBody") or next(iter(styles.values())),
            ))
            story.append(Spacer(1, 6))

    rows = [["신살", "위치", "지지", "설명"]]
    for item in items[:10]:
        rows.append([
            str(item.get("name", "")),
            str(item.get("where", "")),
            str(item.get("branch", "")),
            str(item.get("detail", "")),
        ])

    font_name = "NotoSansKR"
    for k in ("KBody", "KTitle"):
        st = styles.get(k)
        if st and hasattr(st, "fontName"):
            font_name = st.fontName
            break

    tbl = Table(rows, colWidths=["25%", "15%", "15%", "45%"], hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FFF3E0")),
        ("BACKGROUND", (0, 1), (0, -1), colors.whitesmoke),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#cccccc")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.whitesmoke),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 12))


def _append_samjae_box(story, styles, report: dict) -> None:
    tf = (report.get("extra", {}) or {}).get("total_fortune", {}) or {}
    samjae = tf.get("samjae", {}) or {}

    story.append(Paragraph("삼재/복삼재 요약", styles.get("KTitle") or next(iter(styles.values()))))
    story.append(Spacer(1, 6))

    if not isinstance(samjae, dict) or not samjae:
        story.append(Paragraph("삼재 정보가 없습니다.", styles.get("KBody") or next(iter(styles.values()))))
        story.append(Spacer(1, 10))
        return

    is_samjae = samjae.get("is_samjae")
    phase = samjae.get("stage") or samjae.get("phase") or "-"
    mode = samjae.get("mode") or "NONE"
    risk_level = samjae.get("risk_level")
    relief = samjae.get("relief_score")
    risk = samjae.get("risk_score")

    mode_ko = {
        "NONE": "해당 없음",
        "NORMAL": "일반삼재",
        "MITIGATED": "완화삼재",
        "TRANSFORM": "전환삼재(복삼재)",
    }.get(mode, mode)

    is_samjae_ko = "예" if is_samjae is True else "아니오" if is_samjae is False else "-"

    rows = [
        ["삼재 해당", is_samjae_ko],
        ["단계", str(phase)],
        ["구분", mode_ko],
        ["리스크 레벨(1~3)", str(risk_level) if risk_level is not None else "-"],
        ["완화 점수", str(relief) if relief is not None else "-"],
        ["리스크 점수", str(risk) if risk is not None else "-"],
    ]

    tbl = Table(rows, colWidths=["28%", "72%"], hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "NotoSansKR"),
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
    story.append(Spacer(1, 12))

def _append_monthly_summary_box(story, styles, report: dict) -> None:
    meta = report.get("meta", {}) if isinstance(report, dict) else {}
    y = meta.get("year")
    m = meta.get("month")
    title = f"{y}년 {m}월 핵심 요약" if y and m else "월간 핵심 요약"

    # TODO: 나중에 monthly_report['summary_lines']로 교체
    lines = [
        "• 이번 달의 전반적 흐름: 안정 속 점진적 변화",
        "• 결정 포인트: 서두르지 말고 중순 이후 판단",
        "• 인간관계: 오해보다는 조율에 유리",
        "• 재물/일: 소소한 성과 누적형",
    ]
    _append_monthly_summary_box_titled(story, styles, title=title, lines=lines)


def _append_monthly_summary_boxes(story, styles, monthly_reports: list[dict]) -> None:
    if not monthly_reports:
        return
    first = monthly_reports[0] if isinstance(monthly_reports[0], dict) else {}
    _append_monthly_summary_box(story, styles, first)


# -----------------------------
# 4) 폰트/스타일
# -----------------------------
def _register_korean_fonts() -> Dict[str, str]:
    def _is_registered(name: str) -> bool:
        return name in pdfmetrics.getRegisteredFontNames()

    root = Path(__file__).resolve().parents[2]
    fonts_dir = root / "fonts"

    candidates = [
        ("Malgun", fonts_dir / "malgun.ttf"),
        ("MalgunBold", fonts_dir / "malgunbd.ttf"),
        ("Batang", fonts_dir / "Batang.ttc"),
        ("Gulim", fonts_dir / "Gulim.ttc"),
        ("Malgun", Path(r"C:\Windows\Fonts\malgun.ttf")),
        ("MalgunBold", Path(r"C:\Windows\Fonts\malgunbd.ttf")),
        ("Batang", Path(r"C:\Windows\Fonts\batang.ttc")),
        ("Gulim", Path(r"C:\Windows\Fonts\gulim.ttc")),
    ]

    for fname, fpath in candidates:
        try:
            if _is_registered(fname):
                continue
            if fpath.exists():
                pdfmetrics.registerFont(TTFont(fname, str(fpath)))
        except Exception:
            pass

    normal = "Helvetica"
    bold = "Helvetica-Bold"

    if _is_registered("Malgun"):
        normal = "Malgun"
        bold = "MalgunBold" if _is_registered("MalgunBold") else "Malgun"
        try:
            pdfmetrics.registerFontFamily("Malgun", normal=normal, bold=bold, italic=normal, boldItalic=bold)
        except Exception:
            pass
        return {"normal": normal, "bold": bold}

    if _is_registered("Batang"):
        return {"normal": "Batang", "bold": "Batang"}
    if _is_registered("Gulim"):
        return {"normal": "Gulim", "bold": "Gulim"}

    return {"normal": normal, "bold": bold}


def _make_styles() -> Dict[str, ParagraphStyle]:
    fonts = _register_korean_fonts()
    KFONT = fonts["normal"]
    KFONT_BOLD = fonts["bold"]

    base = getSampleStyleSheet()
    for k in list(base.byName.keys()):
        try:
            base[k].fontName = KFONT
        except Exception:
            pass

    return {
        "KTitle": ParagraphStyle("KTitle", parent=base["Heading2"], fontName=KFONT_BOLD, fontSize=14, leading=18, spaceAfter=8),
        "KSection": ParagraphStyle("KSection", parent=base["Heading3"], fontName=KFONT_BOLD, fontSize=12.5, leading=16, spaceBefore=10, spaceAfter=6),
        "KBody": ParagraphStyle("KBody", parent=base["BodyText"], fontName=KFONT, fontSize=10.5, leading=14, spaceAfter=4),
        "KSmall": ParagraphStyle("KSmall", parent=base["BodyText"], fontName=KFONT, fontSize=9.5, leading=12.5, spaceAfter=2),
        "KBullet": ParagraphStyle("KBullet", parent=base["BodyText"], fontName=KFONT, fontSize=10.5, leading=14, leftIndent=10, spaceAfter=2),
    }


def _add_bullets(story, styles: Dict[str, ParagraphStyle], bullets):
    if not bullets:
        return
    items = []
    for b in bullets:
        if not b:
            continue
        items.append(ListItem(Paragraph(str(b), styles["KBullet"]), leftIndent=0))
    story.append(
        ListFlowable(
            items,
            bulletType="bullet",
            leftIndent=10,
            bulletFontName=styles["KBullet"].fontName,
            bulletFontSize=styles["KBullet"].fontSize,
            bulletOffsetY=-2,
            spaceBefore=2,
            spaceAfter=6,
        )
    )


# -----------------------------
# 5) birth_resolved 출력용 포맷
# -----------------------------
def _fmt_solar(v: object) -> str:
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, dict):
        y = v.get("y"); m = v.get("m"); d = v.get("d")
        hh = v.get("hh"); mi = v.get("mm")
        if y and m and d:
            if hh is not None and mi is not None:
                return f"{int(y):04d}-{int(m):02d}-{int(d):02d} {int(hh):02d}:{int(mi):02d}"
            return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
    return ""


def _fmt_lunar(lunar: dict | None) -> str:
    """
    입력 허용 형태:
      A) {"y":1989,"m":12,"d":5,"is_leap":True}
      B) {"year":1989,"month":12,"day":5,"is_leap":True}
      C) {"lunar_date":"1989-12-05","leap":False}
    """
    if isinstance(lunar, str):
        return lunar.strip()

    if not isinstance(lunar, dict):
        return ""

    # 1) "lunar_date" 문자열 우선 처리
    date_s = lunar.get("lunar_date") or lunar.get("lunarDate") or lunar.get("date")
    if isinstance(date_s, str) and date_s.strip():
        # 윤달 여부 키도 여러 형태 지원
        is_leap = bool(
            lunar.get("is_leap")
            or lunar.get("isLeap")
            or lunar.get("leap")
            or lunar.get("leap_month")
            or lunar.get("is_intercalation")
            or lunar.get("isIntercalation")
        )
        return f"{date_s.strip()}{' (윤달)' if is_leap else ''}"

    # 2) y/m/d or year/month/day 처리
    y = lunar.get("y") or lunar.get("ly") or lunar.get("year")
    m = lunar.get("m") or lunar.get("lm") or lunar.get("month")
    d = lunar.get("d") or lunar.get("ld") or lunar.get("day")

   
    def _to_int(v):
        try:
            return int(float(v))
        except Exception:
            return None

    y = _to_int(y)
    m = _to_int(m)
    d = _to_int(d)

    if not (y and m and d):
        return ""

    is_leap = bool(
        lunar.get("is_leap")
        or lunar.get("isLeap")
        or lunar.get("leap")
        or lunar.get("leap_month")
        or lunar.get("is_intercalation")
        or lunar.get("isIntercalation")
    )

    return f"{y:04d}-{m:02d}-{d:02d}{' (윤달)' if is_leap else ''}"





# -----------------------------
# 6) 외부 진입점(안전판)
# -----------------------------
def build_full_report(
    *,
    name: str,
    birth: str,
    sex: str,
    calendar: str = "solar",
    out_path: str | Path = "out/report.pdf",
    report_kind: str = "monthly",
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> Dict[str, Any]:
    """
    ✅ 지금 목표: "표지에 양/음력 표시 + 월간 요약 1페이지"
    엔진까지 붙이는 건 다음 단계에서 별도 진행.
    """
    solar: dict[str, Any] = {}
    try:
        dt = datetime.strptime(birth.strip(), "%Y-%m-%d %H:%M")
        solar = {"y": dt.year, "m": dt.month, "d": dt.day, "hh": dt.hour, "mm": dt.minute}
    except Exception:
        solar = {}

    lunar = _calc_lunar_from_birth(birth)

    report: Dict[str, Any] = {
        "profile": {"name": name, "sex": sex, "birth": birth, "calendar": calendar},
        "birth_str": birth,
        "birth_resolved": {
            "input": {"birth": birth, "calendar": calendar},
            "solar": solar,
            "lunar": lunar,
        },
        "meta": {
            "report_kind": report_kind,
            "year": year,
            "month": month,
        },
    }

    pdf_path = _build_pdf_report(report=report, out_path=out_path)
    return {"pdf_path": str(pdf_path), "report": report}


# -----------------------------
# 7) PDF 빌더
# -----------------------------
def _build_pdf_report(
    report: Dict[str, Any],
    out_path: str | Path = "out/OUT_LUNAR_CHECK.pdf",
    title: Optional[str] = None,
) -> str:
    out_path = str(Path(out_path))
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    styles = _make_styles()
    ensure_month_styles(styles)

    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    story: list[Any] = []

    # -------------------------
    # 0) report 방어
    # -------------------------
    report = report if isinstance(report, dict) else {}

    # -------------------------
    # 1) user_card / profile / meta 방어
    # -------------------------
    user_card = report.get("user_card")
    user_card = user_card if isinstance(user_card, dict) else {}

    profile = report.get("profile")
    profile = profile if isinstance(profile, dict) else {}

    meta = report.get("meta")
    meta = meta if isinstance(meta, dict) else {}

    # created_at_kst는 meta에 없을 때만 채움(덮어쓰기 금지)
    if "created_at_kst" not in meta:
        meta["created_at_kst"] = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")
    report["meta"] = meta

    # -------------------------
    # 2) 표지용 name / kind / ym_line
    # -------------------------
    name_str = _pick_str(
        user_card.get("name"),
        profile.get("name"),
        report.get("name") if isinstance(report.get("name"), str) else "",
        "Unknown",
    )

    kind = str(meta.get("report_kind") or "").strip()
    cover_title = "운트임 리포트"
    ym_line = ""
    if kind == "monthly":
        y = meta.get("year")
        m = meta.get("month")
        if y and m:
            ym_line = f"{int(float(y))}년 {int(float(m)):02d}월"
            cover_title = "운트임 월간 리포트"
        else:
            cover_title = "운트임 월간 리포트"

    # -------------------------
    # 3) birth_resolved / birth(표지용) 구성
    #    - birth_resolved 는 dict로 보장
    #    - birth 는 birth_resolved 를 우선 사용
    # -------------------------
    birth_resolved = report.get("birth_resolved")
    birth_resolved = birth_resolved if isinstance(birth_resolved, dict) else {}
    report["birth_resolved"] = birth_resolved

    # 표지에서 사용할 birth dict (solar/lunar를 가지고 있는 dict)
    # 우선순위: user_card.birth(dict) -> birth_resolved(dict)
    birth = user_card.get("birth") if isinstance(user_card.get("birth"), dict) else {}
    if not birth:
        birth = birth_resolved
    if not isinstance(birth, dict):
        birth = {}

    # -------------------------
    # 4) 표지용 solar_s / lunar_s 를 "먼저" 확정 (UnboundLocal 방지)
    # -------------------------
    br = birth if isinstance(birth, dict) else {}
    
    # =========================================================
    # [FIX] PDF 생성 시점에 입력 birth_str로 solar/lunar 재계산
    #       (엔진 birth_resolved.lunar가 틀려도 PDF는 항상 정답)
    # =========================================================
    profile = report.get("profile", {}) if isinstance(report, dict) else {}
    user_card = report.get("user_card", {}) if isinstance(report.get("user_card"), dict) else {}

    birth_input = _pick_str(
        report.get("birth_str") if isinstance(report, dict) else "",
        profile.get("birth") if isinstance(profile, dict) else "",
        user_card.get("birth_str") if isinstance(user_card, dict) else "",
        user_card.get("birth") if isinstance(user_card, dict) and isinstance(user_card.get("birth"), str) else "",
    )

    # solar dict 재구성 (입력 문자열 기준)
    solar_calc: dict[str, Any] = {}
    try:
        dt_in = datetime.strptime(birth_input.strip(), "%Y-%m-%d %H:%M")
        solar_calc = {"y": dt_in.year, "m": dt_in.month, "d": dt_in.day, "hh": dt_in.hour, "mm": dt_in.minute}
    except Exception:
        solar_calc = {}

    # lunar dict 재계산 (입력 문자열 기준)
    lunar_calc = _calc_lunar_from_birth(birth_input) if birth_input else None

    # report.birth_resolved에 강제 반영
    br_all = report.setdefault("birth_resolved", {}) if isinstance(report, dict) else {}
    if isinstance(br_all, dict):
        if solar_calc:
            br_all["solar"] = solar_calc
        if lunar_calc:
            br_all["lunar"] = lunar_calc

    # solar_s
    solar_s = ""
    # 1) birth_resolved에서 미리 만든 solar_str가 있으면 우선 사용
    if isinstance(birth_resolved.get("solar_str"), str):
        solar_s = birth_resolved.get("solar_str", "").strip()
    # 2) 없으면 solar dict 포맷
    if not solar_s:
        solar_s = _fmt_solar(br.get("solar"))

    # 그래도 비면 birth_str/birth로 최소 보정
    if not solar_s:
        solar_s = _pick_str(
            report.get("birth_str") if isinstance(report.get("birth_str"), str) else "",
            report.get("birth") if isinstance(report.get("birth"), str) else "",
            "",
        )

    # lunar_s
    lunar_s = ""
    # 1) birth_resolved에서 미리 만든 lunar_str가 있으면 우선
    if isinstance(birth_resolved.get("lunar_str"), str):
        lunar_s = birth_resolved.get("lunar_str", "").strip()
    # 2) 없으면 lunar dict 포맷 (birth_resolved.lunar 가 정답)
    if not lunar_s:
        lunar_s = _fmt_lunar(br.get("lunar") or birth_resolved.get("lunar"))

    # -------------------------
    # 5) 표지 subtitle 구성
    # -------------------------
    birth_display_parts: list[str] = []
    if solar_s:
        birth_display_parts.append(f"양력 {solar_s}")
    if lunar_s:
        birth_display_parts.append(f"음력 {lunar_s}")
    birth_display = " / ".join([s for s in birth_display_parts if s])

    cover_sub = [
        ym_line,
        f"이름: {name_str or 'Unknown'}",
        f"생년월일시: {birth_display}",
    ]
    cover_sub = [s for s in cover_sub if isinstance(s, str) and s.strip()]

    _append_cover_page(story, styles, title=cover_title, subtitle_lines=cover_sub)

    # -------------------------
    # 6) 2페이지 - 사용자 요약 카드
    #    (user_card가 비는 문제 방지: 최소 키 강제)
    # -------------------------
    story.append(PageBreak())

    # profile 보정
    _name = profile.get("name") or report.get("name") or user_card.get("name") or "Unknown"
    _sex = profile.get("sex") or report.get("sex") or user_card.get("sex") or ""
    profile["name"] = _name
    profile["sex"] = _sex
    report["profile"] = profile

    # user_card 보정 (무조건 문자열로 넣어서 표가 안전하게 출력되게)
    uc = report.get("user_card", {})
    uc = uc if isinstance(uc, dict) else {}

    uc["name"] = _name
    uc["sex"] = _sex
    uc["gender"] = uc.get("gender") or uc.get("sex") or ""

    # ✅ 여기서 br["solar_str"], br["lunar_str"] 만들어둔 값을 사용
    br2 = report.get("birth_resolved", {})
    solar_str = br2.get("solar_str") or _fmt_solar(br2.get("solar"))
    lunar_str = br2.get("lunar_str") or _fmt_lunar(br2.get("lunar"))

    uc["solar"] = str(solar_str or "")
    uc["lunar"] = str(lunar_str or "")
    uc["meta"] = {"created_at_kst": meta.get("created_at_kst", "")}

    # ✅ user_card에 사주 기둥(pillars) 강제 연결

    src_pillars = None

    # 1) report 최상위에 pillars 있으면 사용
    if isinstance(report.get("pillars"), dict):
        src_pillars = report.get("pillars")

    # 2) 없으면 analysis 안에서 찾기
    if not isinstance(src_pillars, dict):
        analysis = report.get("analysis")
        if isinstance(analysis, dict) and isinstance(analysis.get("pillars"), dict):
            src_pillars = analysis.get("pillars")


    uc["pillars"] = src_pillars if isinstance(src_pillars, dict) else {}

    # 🔥 핵심: report에도 동기화 (PDF 다른 구간에서 사용 가능)
    report["pillars"] = uc["pillars"]
    
    analysis = report.get("analysis")
    if not isinstance(analysis, dict):
        analysis = {}
    report["analysis"] = analysis
    report["analysis"]["pillars"] = report["pillars"]

    report["user_card"] = uc

    # 사주 핵심 요약: 표 grid 최소화 카드 UI (report_styles_common.build_counsel_card, TOP3와 동일 규칙)
    try:
        from reports.saju_color_boxes import append_saju_color_dashboard

        append_saju_color_dashboard(story, styles, report)
    except Exception as e:
        story.append(
            Paragraph(
                f"[WARN] 사주 핵심 요약 박스 생략: {type(e).__name__}: {e}",
                styles.get("KBody") or styles.get("BodyText") or styles.get("Normal"),
            )
        )
        story.append(Spacer(1, 6))

    story.append(PageBreak())
    _append_user_card_summary_page(story, styles, report, report.get("user_card", {}))

    # -------------------------
    # 6b) 연간 운세 + 양력 1~12월 월운 (총운/핵심 요약과 별도)
    # -------------------------
    if append_calendar_fortune_sections is not None:
        try:
            append_calendar_fortune_sections(story, styles, report)
        except Exception as e:
            story.append(
                Paragraph(
                    f"[WARN] 연간/월별 운세 섹션 생략: {type(e).__name__}: {e}",
                    styles.get("KBody") or styles.get("BodyText") or next(iter(styles.values())),
                )
            )
            story.append(Spacer(1, 6))

    # -------------------------
    # 7) 이후 페이지 — 월간 번들 등
    # -------------------------
    story.append(PageBreak())

    # --- 월간 번들(Top3 포함) ---------------------------------
    if report_monthly_bundle is not None:
        try:
            report_monthly_bundle(story, styles, report)
        except Exception as e:
            # 월간 번들이 실패해도 PDF가 죽지 않게 방어
            story.append(
                Paragraph(
                    f"[WARN] monthly_bundle section skipped: {type(e).__name__}: {e}",
                    styles.get("KBody") or next(iter(styles.values())),
                )
            )
            story.append(Spacer(1, 6))
            _append_monthly_summary_box(story, styles, report)
    else:
        _append_monthly_summary_box(story, styles, report)

        # ✅ 오행 분포 추가
        _append_oheng_section(story, styles, report)
        # ✅ 신살 분석 추가
        _append_shinsal_section(story, styles, report)
        # ✅ 삼재 출력 추가
        _append_samjae_box(story, styles, report)
    
    # ✅ Top3는 월간 번들 성공/실패와 무관하게 “항상” 한 번 더 시도(강제 출력)
    try:
        from reports.monthly_report import _append_top3_month_patterns_cards

        mb2 = report.get("monthly_bundle") if isinstance(report, dict) else {}
        if not isinstance(mb2, dict):
            mb2 = {}

        _append_top3_month_patterns_cards(story, styles, report, mb2)

    except Exception as e:
        # Top3도 실패하면 조용히 스킵(보고서 전체는 유지)
        story.append(
            Paragraph(
                f"[WARN] top3 section skipped: {type(e).__name__}: {e}",
                styles.get("KSmall") or styles.get("KBody") or next(iter(styles.values())),
            )
        )
        story.append(Spacer(1, 6))



    if report_month_commentary is not None:
        try:
            report_month_commentary(story, styles, report)
        except Exception as e:
            story.append(Paragraph(f"[WARN] month_commentary section skipped: {type(e).__name__}", styles["KSmall"]))
            story.append(Spacer(1, 6))
    
    # === 사주 요약 (해석 페이지 상단 연결) ===
    pillars = {}

    if isinstance(report, dict):
        # 1) report["pillars"]
        p1 = report.get("pillars")
        if isinstance(p1, dict) and p1:
            pillars = p1

        # 2) report["analysis"]["pillars"]
        if not pillars:
            a = report.get("analysis")
            if isinstance(a, dict):
                p2 = a.get("pillars")
                if isinstance(p2, dict) and p2:
                    pillars = p2

        # 3) report["user_card"]["pillars"]
        if not pillars:
            uc2 = report.get("user_card")
            if isinstance(uc2, dict):
                p3 = uc2.get("pillars")
                if isinstance(p3, dict) and p3:
                    pillars = p3


    def _gj1(pillars: dict, key: str) -> str:
        p = pillars.get(key)

        # 1) dict 형태 {"gan":..., "ji":...}
        if isinstance(p, dict):
            g = str(p.get("gan") or "").strip()
            j = str(p.get("ji") or "").strip()
            s = (g + j).strip()
            return s if s else "미입력"

        # 2) GanJi 같은 객체(gan/ji 속성)
        try:
            g = str(getattr(p, "gan", "") or "").strip()
            j = str(getattr(p, "ji", "") or "").strip()
            s = (g + j).strip()
            if s:
                return s
        except Exception:
            pass

        # 3) 문자열 "갑자" 같은 형태
        if isinstance(p, str) and p.strip():
            return p.strip()

        # 4) 튜플/리스트 ("갑","자")
        if isinstance(p, (tuple, list)) and len(p) >= 2:
            g = str(p[0] or "").strip()
            j = str(p[1] or "").strip()
            s = (g + j).strip()
            return s if s else "미입력"

        return "미입력"


    year_s  = _gj1(pillars, "year")
    month_s = _gj1(pillars, "month")
    day_s   = _gj1(pillars, "day")
    hour_s  = _gj1(pillars, "hour")

    pillars_line = f"년주 {year_s} | 월주 {month_s} | 일주 {day_s} | 시주 {hour_s}"
    p_style = styles.get("Body") or styles.get("Small") or next(iter(styles.values()))
    story.append(Paragraph(f"<b>[사주 요약]</b> {pillars_line}", p_style))
    story.append(Spacer(1, 8))

    for fn, sec_name in [
        (report_year_commentary, "year_commentary"),
        (report_day_commentary, "day_commentary"),
    ]:
        if fn is None:
            continue
        try:
            fn(story, styles, report)
        except Exception as e:
            story.append(Paragraph(f"[WARN] {sec_name} section skipped: {type(e).__name__}", styles["KSmall"]))
            story.append(Spacer(1, 6))

    # --- 선택형 주제 리포트 (기본 리포트와 분리, 후반부) ---
    if append_selected_topic_sections is not None:
        try:
            append_selected_topic_sections(story, styles, report)
        except Exception as e:
            story.append(
                Paragraph(
                    f"[WARN] 선택형 주제 섹션 생략: {type(e).__name__}: {e}",
                    styles.get("KSmall") or styles.get("KBody") or next(iter(styles.values())),
                )
            )
            story.append(Spacer(1, 6))

    doc.build(story)
    return out_path


# --- user_card summary page (PDF) --------------------------------------------

def _safe_get(d: object, key: str, default=None):
    if isinstance(d, dict):
        return d.get(key, default)
    return default


def _pillars_to_rows(pillars: object):
    """
    pillars: {"year":{"gan":"甲","ji":"子"}, "month":..., "day":..., "hour":...}
    -> table rows for PDF
    """
    if not isinstance(pillars, dict):
        pillars = {}

    def gj(k: str):
        item = pillars.get(k) if isinstance(pillars, dict) else None
        if not isinstance(item, dict):
            return ("", "")
        gan = str(item.get("gan") or "").strip()
        ji = str(item.get("ji") or "").strip()
        return (gan, ji)

    y_g, y_j = gj("year")
    m_g, m_j = gj("month")
    d_g, d_j = gj("day")
    h_g, h_j = gj("hour")

    # 헤더 + 2줄(천간/지지)
    return [
        ["", "년", "월", "일", "시"],
        ["천간", y_g, m_g, d_g, h_g],
        ["지지", y_j, m_j, d_j, h_j],
    ]


def _append_user_card_summary_page(story, styles, report: dict, user_card: dict):

    """
    PDF 2페이지에 들어갈 '사용자 요약 카드' 1장
    - styles가 dict/StyleSheet 어느 쪽이든 안전
    - 한글 폰트 등록을 이 함수에서도 보장(검은 네모 방지)
    """
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.pdfbase import pdfmetrics
    from reportlab.lib.styles import ParagraphStyle

    # 0) 폰트 보장(중요: build_pdf_report를 안 거쳐도 안전)
    try:
        from reports.report_styles_common import ensure_report_fonts
        ensure_report_fonts()
    except Exception:
        pass

    # user_card 방어
    if not isinstance(user_card, dict):
        user_card = {}

    # 1) 값 추출
    name = str(user_card.get("name") or "Unknown").strip()
    gender = str(user_card.get("gender") or "").strip()
    solar = str(user_card.get("solar") or "").strip()
    lunar = str(user_card.get("lunar") or "").strip()

    _meta_raw = user_card.get("meta")
    meta: Dict[str, Any] = _meta_raw if isinstance(_meta_raw, dict) else {}
    created = str(meta.get("created_at_kst") or "").strip()
    # ISO가 길면 날짜+시간만 잘라서 보기 좋게
    if len(created) >= 19:
        created = created[:19].replace("T", " ")

    _pillars_raw = user_card.get("pillars")
    pillars: Dict[str, Any] = _pillars_raw if isinstance(_pillars_raw, dict) else {}

    # --- pillars fallback (없으면 report에서 다시 가져오기) ---
    if not pillars:
        src_pillars = report.get("pillars")
        if not isinstance(src_pillars, dict):
            analysis_any = report.get("analysis")
            src_pillars = (
                analysis_any.get("pillars")
                if isinstance(analysis_any, dict)
                else None
            )

        if isinstance(src_pillars, dict):
            pillars = src_pillars
            user_card["pillars"] = pillars
    # -------------------------------------------------------------

    # 2) styles 안전 getter
    ss = getSampleStyleSheet()

    def _style_get(key: str, fallback_key: str):
        try:
            if isinstance(styles, dict):
                return styles.get(key) or styles.get(fallback_key) or ss[fallback_key]
            # StyleSheet 계열
            if hasattr(styles, "__getitem__"):
                try:
                    return styles[key]
                except Exception:
                    return styles[fallback_key]
        except Exception:
            return ss[fallback_key]

    H2_STYLE = _style_get("H2", "Heading2")
    NORMAL_STYLE = _style_get("Normal", "Normal")

    # 3) 한글 폰트 선택 (등록된 폰트 중 한국어 폰트 우선)
    def _pick_korean_font() -> str:
        regs = set()
        try:
            regs = set(pdfmetrics.getRegisteredFontNames())
        except Exception:
            regs = set()

        candidates = [
            "NotoSansKR",
            "NotoSansKR-Regular",
            "Noto Sans KR",
            "NotoSansCJKkr-Regular",
            "NotoSansCJKkr",
        ]
        for fn in candidates:
            if fn in regs:
                return fn
        # fallback
        try:
            return getattr(NORMAL_STYLE, "fontName", "Helvetica")
        except Exception:
            return "Helvetica"

    base_font = _pick_korean_font()

    # 4) Paragraph 스타일(한글 강제)
    H2_KR = ParagraphStyle("H2_KR", parent=H2_STYLE, fontName=base_font)
    NORMAL_KR = ParagraphStyle("NORMAL_KR", parent=NORMAL_STYLE, fontName=base_font)

    def P(text: str) -> Paragraph:
        return Paragraph(str(text), NORMAL_KR)

    # 5) 제목
    story.append(Paragraph("사용자 요약 카드", H2_KR))
    story.append(Spacer(1, 10))

    # 6) 상단 정보 카드(이름/성별/양력/음력/생성일)
    info_data = [
        [P("이름"), P(name)],
        [P("성별"), P(gender)],
        [P("양력"), P(solar)],
        [P("음력"), P(lunar)],
        [P("생성일"), P(created)],
    ]

    info_tbl = Table(info_data, colWidths=[90, 420])
    info_tbl.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), base_font),   # ✅ 전체 폰트 강제
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#DDDDDD")),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#333333")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#DDDDDD")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F3F3F3")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(info_tbl)
    story.append(Spacer(1, 14))

    # 사주 4기둥·오행·십신 등은 앞 페이지「사주 핵심 요약」컬러 박스를 사용 (회색 간단표 제거)
    story.append(Paragraph("사주 기둥·오행·십신·신살·십이운성·공망·용신은 앞 페이지의 <b>사주 핵심 요약</b>을 참고하세요.", NORMAL_KR))
    story.append(Spacer(1, 10))

# ------------------------------------------------------------
# public alias (for imports)
# ------------------------------------------------------------
def build_pdf_report(
    report: dict,
    out_path: str = "out/out_report.pdf",
    title: str | None = None,
) -> str:
    """
    외부에서 호출하는 공식 PDF 생성 엔트리 포인트.

    - 폰트(한글 깨짐 방지)를 먼저 보장
    - 내부 구현(_build_pdf_report)로 위임
    """
    # 폰트 보장 (한글 깨짐 방지)
    try:
        from reports.report_styles_common import ensure_report_fonts
        ensure_report_fonts()
    except Exception:
        # 폰트 보장은 실패해도 PDF 생성 자체는 진행
        pass

    return _build_pdf_report(
        report=report,
        out_path=out_path,
        title=title,
    )

