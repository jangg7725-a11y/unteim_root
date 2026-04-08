# -*- coding: utf-8 -*-

from __future__ import annotations
from typing import Any, Dict, List

ELEMENTS = ["木","火","土","金","水"]


def _element_score(row: Dict[str, Any]) -> Dict[str, Any]:
    raw = row.get("element_score")
    return raw if isinstance(raw, dict) else {}


def summarize_element_tendency(flows: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = {k: 0.0 for k in ELEMENTS}
    for row in flows:
        sc = _element_score(row)
        for k in ELEMENTS:
            total[k] += float(sc.get(k, 0.0))
    s = sum(total.values()) or 1.0
    ratio = {k: round(total[k] / s, 3) for k in ELEMENTS}
    order = sorted(ratio.items(), key=lambda x: x[1], reverse=True)
    top2 = [order[0][0], order[1][0]]
    weak2 = [order[-2][0], order[-1][0]]
    note = f"{top2[0]}/{top2[1]} 기세가 상대적으로 강함. {weak2[0]}/{weak2[1]}는 약세."
    return {"overall_ratio": ratio, "top_elements": top2, "note": note}

def yearly_headlines(flows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in flows:
        sc = _element_score(row)
        tops = sorted(sc.items(), key=lambda x: float(x[1]), reverse=True)[:2]
        label = "/".join([t[0] for t in tops if t[1] > 0])
        out.append({
            "year": row["year"],
            "headline": f"{label} 기세",
            "dayun_order": row["dayun_order"],
            "dayun_pillar": row["dayun_pillar"],
            "year_pillar": row["year_pillar"],
        })
    return out

def interpret_year(row: Dict[str, Any]) -> str:
    """단일 연도 상세 해석 한 줄"""
    sc = _element_score(row)
    strong = sorted(
        [(k, v) for k, v in sc.items() if float(v) > 0],
        key=lambda x: float(x[1]),
        reverse=True,
    )[:2]
    strong_txt = "/".join([f"{k}({v})" for k, v in strong])
    du = row.get("dayun_pillar")
    yp = row.get("year_pillar")
    du_d = du if isinstance(du, dict) else {}
    yp_d = yp if isinstance(yp, dict) else {}
    return (
        f"{row['year']}년: 대운 {du_d.get('stem', '')}{du_d.get('branch', '')} · "
        f"세운 {yp_d.get('stem', '')}{yp_d.get('branch', '')} → "
        f"강세 {strong_txt}"
    )
