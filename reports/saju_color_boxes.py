# -*- coding: utf-8 -*-
"""
사주 핵심 정보 — 상담 리포트용 카드 UI (ReportLab).
엔진 계산 로직 없음; report dict만 읽어 시각화한다.
표 grid 최소화: report_styles_common.build_counsel_card (TOP3와 동일 규칙) 사용.
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Tuple

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, Paragraph, Spacer, Table, TableStyle

from reports.report_styles_common import build_counsel_card, ensure_report_fonts

# 오행별 부드러운 팔레트 (배경 / 테두리 / 본문)
_ELEM_PALETTE: Dict[str, Tuple[str, str, str]] = {
    "목": ("#E8F5E9", "#81C784", "#1B5E20"),
    "화": ("#FFEBEE", "#E57373", "#B71C1C"),
    "토": ("#FFF8E1", "#FFD54F", "#E65100"),
    "금": ("#ECEFF1", "#90A4AE", "#37474F"),
    "수": ("#E3F2FD", "#64B5F6", "#0D47A1"),
}

_HANJA_ELEM: Dict[str, str] = {
    "甲": "목", "乙": "목", "丙": "화", "丁": "화", "戊": "토", "己": "토",
    "庚": "금", "辛": "금", "壬": "수", "癸": "수",
}
_HANJA_BRANCH_ELEM: Dict[str, str] = {
    "子": "수", "丑": "토", "寅": "목", "卯": "목", "辰": "토", "巳": "화",
    "午": "화", "未": "토", "申": "금", "酉": "금", "戌": "토", "亥": "수",
}

_TEN_NAMES = ("비견", "겁재", "식신", "상관", "편재", "정재", "편관", "정관", "편인", "정인")

# 카드 배경 (TOP3 톤과 맞춤)
_CARD_BG_OHENG = colors.HexColor("#FAFAFA")
_CARD_BG_SIPSIN = colors.HexColor("#FAF7FC")
_CARD_BG_SHINSAL = colors.HexColor("#F5FAF8")
_CARD_BG_KM = colors.HexColor("#F2F5F8")
_CARD_BG_YONG = colors.HexColor("#FCE4EC")  # 용신 강조

# 오행 분포 가로 막대(세그먼트) — 텍스트 ■ 대신 PDF 배경색 사용
_BAR_FILL: Dict[str, colors.Color] = {
    "목": colors.HexColor("#2E7D32"),
    "화": colors.HexColor("#D32F2F"),
    "토": colors.HexColor("#A1887F"),
    "금": colors.HexColor("#90A4AE"),
    "수": colors.HexColor("#1565C0"),
}
_BAR_EMPTY = colors.HexColor("#ECEFF1")
_BAR_BORDER = colors.HexColor("#CFD8DC")


def _hex_to_color(hex_s: str) -> colors.Color:
    return colors.HexColor(hex_s)


def _elem_for_stem(stem: str) -> str:
    s = str(stem).strip()
    return _HANJA_ELEM.get(s, "토")


def _elem_for_branch(br: str) -> str:
    b = str(br).strip()
    return _HANJA_BRANCH_ELEM.get(b, "토")


def _analysis(report: Mapping[str, Any]) -> Dict[str, Any]:
    a = report.get("analysis")
    return a if isinstance(a, dict) else {}


def _pillar_gj(block: Any) -> Tuple[str, str]:
    if not isinstance(block, dict):
        return "", ""
    g = block.get("gan") or block.get("stem") or ""
    j = block.get("ji") or block.get("branch") or ""
    return str(g).strip(), str(j).strip()


def _pillars_map(report: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    p = report.get("pillars")
    if isinstance(p, dict):
        return p
    a = _analysis(report)
    pp = a.get("pillars")
    return pp if isinstance(pp, dict) else {}


def _oheng_counts(report: Mapping[str, Any]) -> Dict[str, float]:
    oh = report.get("oheng")
    if not isinstance(oh, dict):
        oh = _analysis(report).get("oheng")
    oh = oh if isinstance(oh, dict) else {}
    raw = oh.get("counts")
    if not isinstance(raw, dict):
        return {}
    m = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}
    out: Dict[str, float] = {}
    for k, v in raw.items():
        kk = m.get(str(k), str(k))
        if kk in ("목", "화", "토", "금", "수"):
            try:
                out[kk] = float(v)
            except (TypeError, ValueError):
                out[kk] = 0.0
    return out


def _sipsin_counts(report: Mapping[str, Any]) -> Dict[str, float]:
    a = _analysis(report)
    sp = a.get("sipsin")
    if not isinstance(sp, dict):
        return {}
    prof = sp.get("profiles")
    if isinstance(prof, dict) and isinstance(prof.get("counts"), dict):
        raw = prof["counts"]
        out: Dict[str, float] = {}
        for k, v in raw.items():
            try:
                out[str(k)] = float(v)
            except (TypeError, ValueError):
                continue
        return out
    tg = a.get("ten_gods_count_10")
    if isinstance(tg, dict):
        out = {}
        for k, v in tg.items():
            try:
                out[str(k)] = float(v)
            except (TypeError, ValueError):
                continue
        return out
    return {}


def _shinsal_items(report: Mapping[str, Any]) -> List[Dict[str, Any]]:
    sh = report.get("shinsal")
    if not isinstance(sh, dict):
        sh = _analysis(report).get("shinsal")
    if not isinstance(sh, dict):
        return []
    items = sh.get("items")
    if isinstance(items, list):
        return [x for x in items if isinstance(x, dict)]
    return []


def _twelve_block(report: Mapping[str, Any]) -> Dict[str, Any]:
    tf = report.get("twelve_fortunes")
    if tf is None:
        tf = _analysis(report).get("twelve_fortunes")
    return tf if isinstance(tf, dict) else {}


def _kongmang_bits(report: Mapping[str, Any]) -> Tuple[str, str, str]:
    km = report.get("kongmang")
    if km is None:
        km = _analysis(report).get("kongmang")
    void_s = "—"
    flags = "—"
    note = "공망 정보 없음"
    if km is None:
        return void_s, flags, note
    if isinstance(km, dict):
        if km.get("error"):
            return "—", "—", str(km.get("error"))[:120]
        vb = km.get("void_branches")
        if vb is not None:
            try:
                void_s = "·".join(str(x) for x in vb)
            except Exception:
                void_s = str(vb)
        summ = km.get("summary")
        if isinstance(summ, dict):
            natal = summ.get("natal") or ""
            if isinstance(natal, str) and natal.strip():
                note = natal[:220] + ("…" if len(natal) > 220 else "")
        return void_s, flags, note
    vb = getattr(km, "void_branches", None)
    if vb is not None:
        try:
            void_s = "·".join(str(x) for x in vb)
        except Exception:
            void_s = str(vb)
    summ = getattr(km, "summary", None)
    if isinstance(summ, dict):
        natal = summ.get("natal") or ""
        if isinstance(natal, str) and natal.strip():
            note = natal[:220] + ("…" if len(natal) > 220 else "")
    natal_pl = getattr(km, "natal_void_pillars", None) or []
    if isinstance(natal_pl, list) and natal_pl:
        tags = []
        for p in natal_pl:
            if getattr(p, "is_void", False):
                tags.append(f"{getattr(p, 'kind', '?')}")
        if tags:
            flags = ", ".join(tags)
    return void_s, flags, note


def _yong_box(report: Mapping[str, Any]) -> Tuple[str, str, str, str, str]:
    a = _analysis(report)
    ys = a.get("yongshin")
    ys = ys if isinstance(ys, dict) else {}
    y_el = str(ys.get("용신오행") or ys.get("yong_element") or ys.get("용신") or "—")
    h_el = str(ys.get("희신요약") or ys.get("heesin") or "—")
    if h_el == "—":
        he = ys.get("희신오행")
        if isinstance(he, list) and he:
            h_el = ", ".join(str(x) for x in he[:4])
        elif isinstance(he, str):
            h_el = he
    g_el = str(ys.get("기신요약") or ys.get("gisin") or "—")
    if g_el == "—":
        ge = ys.get("기신오행")
        if isinstance(ge, list) and ge:
            g_el = ", ".join(str(x) for x in ge[:4])
        elif isinstance(ge, str):
            g_el = ge
    tip = str(ys.get("실전가이드") or ys.get("tips") or "")[:300]
    if len(tip) > 280:
        tip = tip[:280] + "…"
    sub = str(ys.get("용신해석") or "")[:180]
    return y_el, h_el, g_el, sub, tip


def _pick_font(styles: Any) -> str:
    for k in ("KBody", "KTitle", "Normal"):
        st = None
        if isinstance(styles, dict):
            st = styles.get(k)
        else:
            try:
                st = styles[k]
            except Exception:
                st = None
        if hasattr(st, "fontName") and isinstance(getattr(st, "fontName", None), str):
            return getattr(st, "fontName")
    return "Helvetica"


def _body_style(font: str, styles: Any, size: int = 9) -> ParagraphStyle:
    base = None
    if isinstance(styles, dict):
        base = styles.get("KBody") or styles.get("Normal")
    if base is None:
        base = ParagraphStyle(name="Body", fontName=font, fontSize=size, leading=size + 3)
    return ParagraphStyle(
        name=f"SajuCardBody_{id(object)}",
        parent=base,
        fontName=font,
        fontSize=size,
        leading=size + 3,
        alignment=TA_LEFT,
    )


def _ratio_bar_table(
    ratio: float,
    ek: str,
    *,
    bar_width_mm: float,
    height_pt: float = 9.0,
    n_seg: int = 10,
) -> Table:
    """비율에 따라 채워지는 가로 세그먼트 막대(Table 셀 배경). 문자 막대 미사용."""
    fill = _BAR_FILL.get(ek, colors.HexColor("#78909C"))
    seg_w = bar_width_mm / float(n_seg)
    filled = max(0, min(n_seg, int(round(ratio * n_seg))))
    row = [""] * n_seg
    t = Table([row], colWidths=[seg_w * mm] * n_seg, rowHeights=[height_pt])
    ts: List[Any] = []
    for i in range(n_seg):
        bg = fill if i < filled else _BAR_EMPTY
        ts.append(("BACKGROUND", (i, 0), (i, 0), bg))
    ts.extend(
        [
            ("BOX", (0, 0), (-1, -1), 0.35, _BAR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]
    )
    t.setStyle(TableStyle(ts))
    return t


def _build_oheng_distribution_flowable(
    oc: Dict[str, float],
    total: float,
    strong_el: str,
    weak_el: str,
    *,
    body_st: ParagraphStyle,
    text_w: float,
    bar_w: float,
) -> Table:
    """오행 분포 본문: 왼쪽 수치(Paragraph), 오른쪽 컬러 세그먼트 막대."""
    rows: List[List[Any]] = []
    for ek in ("목", "화", "토", "금", "수"):
        v = float(oc.get(ek, 0.0))
        ratio = (v / total) if total > 0 else 0.0
        if ek == strong_el and strong_el:
            line = (
                f"<b><font color='#AD1457'>{ek}</font> (강)</b> "
                f"{v:.1f} · {ratio * 100:.0f}%"
            )
        elif ek == weak_el and weak_el and ek != strong_el:
            line = (
                f"<font color='#78909C'><b>{ek}</b> (약)</font> "
                f"{v:.1f} · {ratio * 100:.0f}%"
            )
        else:
            line = f"<b>{ek}</b> {v:.1f} · {ratio * 100:.0f}%"
        p = Paragraph(line, body_st)
        bar = _ratio_bar_table(ratio, ek, bar_width_mm=bar_w)
        rows.append([p, bar])

    if not rows:
        return Table(
            [[Paragraph("오행 집계 없음", body_st)]],
            colWidths=[(text_w + bar_w) * mm],
        )

    ot = Table(rows, colWidths=[text_w * mm, bar_w * mm])
    ot.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return ot


def _two_col_row(left: Any, right: Any, *, gap_mm: float = 0) -> Table:
    """동일 카드 2단 배치 (본문 폭 A4−좌우 18mm×2 = 174mm 기준)."""
    w = (174 * mm - gap_mm) / 2.0
    t = Table([[left, right]], colWidths=[w, w])
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return t


def append_saju_color_dashboard(story: List[Any], styles: Any, report: Mapping[str, Any]) -> None:
    """report dict 기반 카드형 요약을 story에 추가한다."""
    ensure_report_fonts()
    font = _pick_font(styles)
    try:
        from reportlab.pdfbase import pdfmetrics

        if font not in pdfmetrics.getRegisteredFontNames():
            font = "Helvetica"
    except Exception:
        font = "Helvetica"

    body_st = _body_style(font, styles, 9)
    title_st = _body_style(font, styles, 11)
    small_st = _body_style(font, styles, 8)

    story.append(Paragraph("<b><font color='#1A237E'>사주 핵심 요약</font></b>", title_st))
    story.append(Spacer(1, 3))
    story.append(
        Paragraph(
            "오행·십신·신살·십이운성·공망·용신을 카드 형태로 정리했습니다.",
            small_st,
        )
    )
    story.append(Spacer(1, 8))

    # ----- 4기둥: 카드 4개 한 줄 -----
    pm = _pillars_map(report)
    order = ("year", "month", "day", "hour")
    labels_k = ("년주", "월주", "일주", "시주")
    pillar_cards: List[Any] = []
    for i, key in enumerate(order):
        g, j = _pillar_gj(pm.get(key))
        eg = _elem_for_stem(g) if g else "토"
        ej = _elem_for_branch(j) if j else "토"
        _, _, fg_g = _ELEM_PALETTE.get(eg, _ELEM_PALETTE["토"])
        _, _, fg_j = _ELEM_PALETTE.get(ej, _ELEM_PALETTE["토"])
        body = (
            f"천간 <b><font color='{fg_g}'>{g or '—'}</font></b> "
            f"<font size=7 color='#78909C'>({eg})</font><br/>"
            f"지지 <b><font color='{fg_j}'>{j or '—'}</font></b> "
            f"<font size=7 color='#78909C'>({ej})</font>"
        )
        title = f"<font color='#37474F'><b>{labels_k[i]}</b></font>"
        if key == "day":
            title = f"<font color='#37474F'><b>{labels_k[i]}</b></font> <font size=7 color='#C62828'>(핵심)</font>"
        brd = 2.0 if key == "day" else 1.2
        brd_c = colors.HexColor("#5C6BC0") if key == "day" else None
        pillar_cards.append(
            build_counsel_card(
                title,
                body,
                font_name=font,
                paragraph_style=body_st,
                bg=_hex_to_color(_ELEM_PALETTE.get(eg, _ELEM_PALETTE["토"])[0]),
                col_width="100%",
                border_color=brd_c or colors.HexColor("#B0BEC5"),
                border_w=brd,
                pad=10,
                vpad=8,
            )
        )
    row_p = Table([pillar_cards], colWidths=[42 * mm, 42 * mm, 42 * mm, 42 * mm])
    row_p.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    story.append(row_p)
    story.append(Spacer(1, 8))

    # ----- 오행 + 십신 (2단 카드) -----
    oc = _oheng_counts(report)
    total = sum(oc.values()) or 1.0
    strong_el = max(oc, key=lambda k: oc[k]) if oc else ""
    weak_el = min(oc, key=lambda k: oc[k]) if oc else ""
    if strong_el == weak_el and len(oc) <= 1:
        weak_el = ""

    o_body_flow = _build_oheng_distribution_flowable(
        oc,
        total,
        strong_el,
        weak_el,
        body_st=body_st,
        text_w=38.0,
        bar_w=44.0,
    )

    sc = _sipsin_counts(report)
    top3 = sorted(sc.items(), key=lambda x: x[1], reverse=True)[:3]
    top_set = {t[0] for t in top3}
    s_lines: List[str] = []
    for name in _TEN_NAMES:
        v = float(sc.get(name, 0.0))
        if name in top_set:
            s_lines.append(f"<b><font color='#6A1B9A'>{name}</font></b> · {v:.1f}")
        else:
            s_lines.append(f"{name} · {v:.1f}")
    s_body = "<br/>".join(s_lines) if s_lines else "—"

    card_o = build_counsel_card(
        "<font color='#37474F'><b>오행 분포</b></font>",
        "",
        body_flowable=o_body_flow,
        font_name=font,
        paragraph_style=body_st,
        bg=_CARD_BG_OHENG,
        col_width="100%",
        border_w=1.2,
        pad=12,
        vpad=9,
    )
    card_s = build_counsel_card(
        "<font color='#37474F'><b>십신 강도</b></font><br/><font size=7 color='#7E57C2'>상위 십신 강조</font>",
        s_body,
        font_name=font,
        paragraph_style=body_st,
        bg=_CARD_BG_SIPSIN,
        col_width="100%",
        border_w=1.2,
        pad=12,
        vpad=9,
    )
    story.append(_two_col_row(card_o, card_s, gap_mm=4 * mm))
    story.append(Spacer(1, 6))

    # ----- 신살 + 12운성 (2단 카드) -----
    sh_items = _shinsal_items(report)
    by_pillar: Dict[str, List[str]] = {"year": [], "month": [], "day": [], "hour": []}
    for it in sh_items:
        pl = str(it.get("where") or it.get("pillar") or "").strip().lower()
        nm = str(it.get("name") or it.get("label") or "")
        if not nm:
            continue
        if pl in by_pillar:
            by_pillar[pl].append(nm)

    sh_lines_html: List[str] = []
    for pk, lab in (("year", "년"), ("month", "월"), ("day", "일"), ("hour", "시")):
        tags = by_pillar.get(pk, [])
        if tags:
            sh_lines_html.append(
                f"<b>{lab}주</b> · " + " · ".join(f"<b>{t}</b>" for t in tags[:10])
            )
        else:
            sh_lines_html.append(f"<b>{lab}주</b> · <font color='#9E9E9E'>해당 없음</font>")
    sh_body = "<br/>".join(sh_lines_html) if sh_lines_html else "신살 데이터 없음"

    tf = _twelve_block(report)
    t12_lines: List[str] = []
    for key, lab in (("year", "년"), ("month", "월"), ("day", "일"), ("hour", "시")):
        b = tf.get(key)
        if isinstance(b, dict):
            br = str(b.get("branch") or "")
            fo = str(b.get("fortune") or "")
        else:
            br, fo = "", ""
        t12_lines.append(f"<b>{lab}주</b> {br or '—'} · <i>{fo or '—'}</i>")
    t12_body = "<br/>".join(t12_lines)

    card_sh = build_counsel_card(
        "<font color='#37474F'><b>신살</b></font>",
        sh_body,
        font_name=font,
        paragraph_style=body_st,
        bg=_CARD_BG_SHINSAL,
        col_width="100%",
        border_w=1.2,
        pad=12,
        vpad=9,
    )
    card_t12 = build_counsel_card(
        "<font color='#37474F'><b>십이운성</b></font><br/><font size=7 color='#00897B'>(일간 기준)</font>",
        t12_body,
        font_name=font,
        paragraph_style=body_st,
        bg=colors.HexColor("#E0F2F1"),
        col_width="100%",
        border_w=1.2,
        pad=12,
        vpad=9,
    )
    story.append(_two_col_row(card_sh, card_t12, gap_mm=4 * mm))
    story.append(Spacer(1, 6))

    # ----- 공망 + 용신 (같은 페이지에 묶음, 용신 카드 최강조) -----
    void_s, void_flags, void_note = _kongmang_bits(report)
    y1, y2, y3, y_sub, y_tip = _yong_box(report)

    km_body = (
        f"<b>공망 지지</b> {void_s}<br/>"
        f"<b>영향 기둥</b> {void_flags}<br/><br/>"
        f"<font size=8 color='#455A64'>{void_note[:420]}</font>"
    )
    card_km = build_counsel_card(
        "<font color='#37474F'><b>공망</b></font>",
        km_body,
        font_name=font,
        paragraph_style=body_st,
        bg=_CARD_BG_KM,
        col_width="100%",
        border_w=1.2,
        pad=12,
        vpad=9,
    )

    ys_body = (
        f"<b><font color='#880E4F'>용신</font></b> {y1}<br/>"
        f"<b>희신</b> {y2}<br/>"
        f"<b>기신</b> {y3}<br/><br/>"
        f"<i><font size=8 color='#5D4037'>{y_sub}</font></i><br/><br/>"
        f"<b>활용 포인트</b><br/><font size=8>{y_tip or '—'}</font>"
    )
    card_ys = build_counsel_card(
        "<font color='#880E4F'><b>용신 · 희신 · 기신</b></font> <font size=7 color='#AD1457'>(핵심)</font>",
        ys_body,
        font_name=font,
        paragraph_style=body_st,
        bg=_CARD_BG_YONG,
        col_width="100%",
        border_color=colors.HexColor("#AD1457"),
        border_w=2.4,
        pad=14,
        vpad=10,
    )

    story.append(
        KeepTogether(
            [
                _two_col_row(card_km, card_ys, gap_mm=4 * mm),
                Spacer(1, 6),
            ]
        )
    )
