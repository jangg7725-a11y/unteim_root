# -*- coding: utf-8 -*-
"""
콘솔 시각화 리포트 (가변 컬럼/정렬/연도 범위)
예)
python -m reports.pretty_report --name OSU --birth "1966-11-04 02:05" --sex F --years 24
python -m reports.pretty_report --name OSU --birth "1966-11-04 02:05" --sex F --from-year 1980 --to-year 2005 --sort top --desc
python -m reports.pretty_report --name OSU --birth "1966-11-04 02:05" --sex F --columns year,order,dayun,yearpillar,top,score
"""

from __future__ import annotations

import argparse
from datetime import datetime
from typing import Any, Dict, List, Union

from engine.lunar_kr import KST
from engine.pillars import calc_four_pillars
from engine.luck import calc_dayun
from engine.flow import build_yearly_flow
from engine.interpret import summarize_element_tendency, yearly_headlines

DEFAULT_COLUMNS = ["year", "dayun", "yearpillar", "top", "score"]

_ELEMENTS = ("木", "火", "土", "金", "水")


def _element_score(row: Dict[str, Any]) -> Dict[str, float]:
    """flow 행에서 element_score를 float dict로 통일."""
    raw = row.get("element_score")
    if not isinstance(raw, dict):
        return {e: 0.0 for e in _ELEMENTS}
    out: Dict[str, float] = {}
    for e in _ELEMENTS:
        try:
            out[e] = float(raw.get(e, 0.0) or 0.0)
        except (TypeError, ValueError):
            out[e] = 0.0
    return out


def _top_elements_label(score: Dict[str, float]) -> str:
    tops = sorted(score.items(), key=lambda x: x[1], reverse=True)[:2]
    tops_k = [k for k, v in tops if float(v) > 0]
    return "/".join(tops_k) if tops_k else "-"


def _fmt_score(d: Dict[str, float]) -> str:
    parts = [f"{k}:{float(v):.1f}" for k, v in d.items()]
    return "{" + ", ".join(parts) + "}"


def _pillar_pair(row: Dict[str, Any], key: str) -> str:
    p = row.get(key)
    if not isinstance(p, dict):
        return "-"
    return f"{p.get('stem', '')}{p.get('branch', '')}"


def _format_row(row: Dict[str, Any], columns: List[str]) -> str:
    score = _element_score(row)
    pieces: List[str] = []
    for col in columns:
        if col == "year":
            pieces.append(str(row.get("year", "")))
        elif col == "order":
            pieces.append(f"DU{row.get('dayun_order', '')}")
        elif col == "dayun":
            pieces.append(_pillar_pair(row, "dayun_pillar"))
        elif col == "yearpillar":
            pieces.append(_pillar_pair(row, "year_pillar"))
        elif col == "top":
            pieces.append(_top_elements_label(score))
        elif col == "score":
            pieces.append(_fmt_score(score))
        elif col == "combined":
            cmb = row.get("combined")
            if isinstance(cmb, dict):
                stems = cmb.get("stems") or []
                brs = cmb.get("branches") or []
                if isinstance(stems, list) and isinstance(brs, list):
                    pieces.append(f"{''.join(str(x) for x in stems)}/{''.join(str(x) for x in brs)}")
                else:
                    pieces.append("-")
            else:
                pieces.append("-")
        else:
            pieces.append("-")
    return " | ".join(pieces)


def _sort_key(row: Dict[str, Any], how: str) -> Union[int, float]:
    sc = _element_score(row)
    if how == "year":
        y = row.get("year", 0)
        return int(y) if isinstance(y, int) else int(y or 0)
    if how == "dayun_order":
        o = row.get("dayun_order", 0)
        return int(o) if isinstance(o, int) else int(o or 0)
    if how == "top":
        vals = sorted(sc.values(), reverse=True)
        return (vals[0] if vals else 0.0) + (vals[1] if len(vals) > 1 else 0.0)
    m = {"wood": "木", "fire": "火", "earth": "土", "metal": "金", "water": "水"}
    if how in m:
        return float(sc.get(m[how], 0.0))
    return float(row.get("year", 0) or 0)


def _safe_dayun_age(dayun: Dict[str, Any]) -> str:
    ymd = dayun.get("start_age_ymd")
    if not isinstance(ymd, dict):
        return "?y ?m ?d"
    return (
        f"{ymd.get('years', 0)}y {ymd.get('months', 0)}m {ymd.get('days', 0)}d"
    )


def _row_year(row: Dict[str, Any]) -> int:
    y = row.get("year", 0)
    if isinstance(y, int):
        return y
    if isinstance(y, float):
        return int(y)
    if isinstance(y, str):
        try:
            return int(y.strip())
        except ValueError:
            return 0
    try:
        return int(y)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True)
    p.add_argument("--birth", required=True, help='예) "1966-11-04 02:05"')
    p.add_argument("--sex", choices=["M", "F"], required=True)
    p.add_argument("--calendar", choices=["solar", "lunar"], default="solar")

    p.add_argument("--years", type=int, default=12, help="대운 시작 연도 기준 표시할 연수")
    p.add_argument("--from-year", type=int, default=None, help="표시 시작 연도(우선순위 높음)")
    p.add_argument("--to-year", type=int, default=None, help="표시 끝 연도(우선순위 높음)")

    p.add_argument(
        "--sort",
        choices=["year", "dayun_order", "top", "wood", "fire", "earth", "metal", "water"],
        default="year",
        help="정렬 기준",
    )
    p.add_argument("--desc", action="store_true", help="내림차순 정렬")

    p.add_argument(
        "--columns",
        default=",".join(DEFAULT_COLUMNS),
        help=f"표시 컬럼 CSV (기본: {','.join(DEFAULT_COLUMNS)}) | "
        "가능: year,order,dayun,yearpillar,top,score,combined",
    )

    args = p.parse_args()

    naive = datetime.strptime(args.birth, "%Y-%m-%d %H:%M")
    birth_kst = KST.localize(naive)

    pillars = calc_four_pillars(birth_kst)
    dayun: Dict[str, Any] = calc_dayun(birth_kst, args.sex, pillars, count=8)

    fy, ty = args.from_year, args.to_year
    if fy is not None and ty is not None:
        flows_all = build_yearly_flow(birth_kst, args.sex, pillars, dayun, span_years=120)
        flows = [r for r in flows_all if isinstance(r, dict) and fy <= _row_year(r) <= ty]
    elif fy is not None:
        flows_all = build_yearly_flow(birth_kst, args.sex, pillars, dayun, span_years=120)
        flows = [r for r in flows_all if isinstance(r, dict) and _row_year(r) >= fy][: args.years]
    elif ty is not None:
        flows_all = build_yearly_flow(birth_kst, args.sex, pillars, dayun, span_years=120)
        base = [r for r in flows_all if isinstance(r, dict) and _row_year(r) <= ty]
        flows = base[-args.years :] if len(base) > args.years else base
    else:
        flows = build_yearly_flow(birth_kst, args.sex, pillars, dayun, span_years=args.years)

    flows_list: List[Dict[str, Any]] = [r for r in flows if isinstance(r, dict)]

    summary = summarize_element_tendency(flows_list)
    headlines = yearly_headlines(flows_list)

    flows_sorted = sorted(
        flows_list, key=lambda r: _sort_key(r, args.sort), reverse=args.desc
    )

    columns = [c.strip() for c in args.columns.split(",") if c.strip()]

    print("=" * 76)
    print(
        f"[운트임 콘솔 리포트]  {args.name} · {args.birth} · sex={args.sex} · cal={args.calendar}"
    )
    print(
        "- 대운 시작: ",
        dayun.get("start_datetime_kst", ""),
        f"({dayun.get('direction', '')}, {_safe_dayun_age(dayun)})",
    )
    print("=" * 76)

    ratio = summary.get("overall_ratio")
    if not isinstance(ratio, dict):
        ratio = {}
    print("\n[오행 비율 요약]")
    print(
        "  木:{:.3f}  火:{:.3f}  土:{:.3f}  金:{:.3f}  水:{:.3f}".format(
            float(ratio.get("木", 0) or 0),
            float(ratio.get("火", 0) or 0),
            float(ratio.get("土", 0) or 0),
            float(ratio.get("金", 0) or 0),
            float(ratio.get("水", 0) or 0),
        )
    )
    print("  →", summary.get("note", ""))

    print(
        f"\n[표] ({'내림차순' if args.desc else '오름차순'} 정렬: {args.sort})  컬럼: {', '.join(columns)}"
    )
    print("-" * 76)
    for row in flows_sorted:
        print(_format_row(row, columns))

    print("\n[연도별 헤드라인]")
    for h in headlines:
        if not isinstance(h, dict):
            continue
        du = h.get("dayun_pillar")
        yp = h.get("year_pillar")
        du_s = f"{du.get('stem', '')}{du.get('branch', '')}" if isinstance(du, dict) else "-"
        ys = f"{yp.get('stem', '')}{yp.get('branch', '')}" if isinstance(yp, dict) else "-"
        print(
            f"  · {h.get('year', '')}: {h.get('headline', '')} (대운 {h.get('dayun_order', '')}회차, "
            f"대운={du_s}, 세운={ys})"
        )


if __name__ == "__main__":
    main()
