# -*- coding: utf-8 -*-
"""
HTML 리포트 생성 (카드+막대 차트)
사용(프로젝트 루트에서):
  python -m reports.html_report --name OSU --birth "1966-11-04 02:05" --sex F --calendar solar --years 24 --out report.html
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime
from typing import Any, Dict, List

from engine.lunar_kr import KST
from engine.pillars import calc_four_pillars
from engine.luck import calc_dayun
from engine.flow import build_yearly_flow
from engine.interpret import summarize_element_tendency

_ELEMENTS = ("木", "火", "土", "金", "水")

TEMPLATE = """<!doctype html><html lang="ko"><meta charset="utf-8">
<title>운트임 리포트 - {name}</title>
<style>
body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,Apple SD Gothic Neo,Noto Sans KR,sans-serif;margin:24px}}
h1{{margin:0 0 8px}} .meta{{color:#555;margin-bottom:16px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px}}
.card{{border:1px solid #eee;border-radius:14px;padding:14px;box-shadow:0 1px 3px rgba(0,0,0,.05)}}
.kv{{display:flex;gap:8px;flex-wrap:wrap;font-size:14px;color:#333}}
.badge{{display:inline-block;background:#f6f7f9;border:1px solid #e5e7eb;border-radius:999px;padding:3px 8px;margin:2px}}
.table{{width:100%;border-collapse:collapse;font-size:14px;margin-top:8px}}
.table th,.table td{{border-bottom:1px solid #eee;padding:6px 8px;text-align:left}}
.barwrap{{display:flex;gap:8px;margin-top:6px}}
.bar{{flex:1;background:#f1f5f9;border-radius:8px;overflow:hidden;height:12px}}
.bar>i{{display:block;height:100%}}
.el{{display:flex;align-items:center;gap:8px}}
.el b{{width:24px;display:inline-block}}
.m{{background:#4ade80}} .h{{background:#f87171}} .t{{background:#facc15}} .g{{background:#93c5fd}} .s{{background:#60a5fa}}
.small{{color:#666;font-size:12px}}
</style>
<h1>운트임 리포트</h1>
<div class="meta">{name} · {birth} · sex={sex} · calendar={calendar}</div>

<div class="grid">
  <div class="card">
    <h3>요약(오행 비율)</h3>
    <div class="el"><b>木</b><div class="bar"><i class="m" style="width:{r_m}%"></i></div><span class="small">{txt_m}</span></div>
    <div class="el"><b>火</b><div class="bar"><i class="h" style="width:{r_h}%"></i></div><span class="small">{txt_h}</span></div>
    <div class="el"><b>土</b><div class="bar"><i class="t" style="width:{r_t}%"></i></div><span class="small">{txt_t}</span></div>
    <div class="el"><b>金</b><div class="bar"><i class="g" style="width:{r_g}%"></i></div><span class="small">{txt_g}</span></div>
    <div class="el"><b>水</b><div class="bar"><i class="s" style="width:{r_s}%"></i></div><span class="small">{txt_s}</span></div>
    <div class="small" style="margin-top:6px">{note}</div>
  </div>

  <div class="card">
    <h3>대운 시작</h3>
    <div class="kv">
      <span class="badge">방향: {du_dir}</span>
      <span class="badge">시작: {du_start}</span>
      <span class="badge">나이: {du_age}</span>
    </div>
  </div>

  <div class="card" style="grid-column:1/-1">
    <h3>연도별 카드({years}년)</h3>
    <table class="table">
      <tr><th>연도</th><th>대운</th><th>세운</th><th>강세 오행</th><th>점수</th></tr>
      {rows}
    </table>
  </div>

</div>
</html>"""


def _ratio_bar_pct(r: Dict[str, Any], key: str) -> int:
    try:
        return int(float(r.get(key, 0)) * 100)
    except (TypeError, ValueError):
        return 0


def _ratio_txt(r: Dict[str, Any], key: str) -> str:
    try:
        return f"{float(r.get(key, 0)):.3f}"
    except (TypeError, ValueError):
        return "—"


def _format_score_cell(sc: Any) -> str:
    if not isinstance(sc, dict):
        return str(sc)
    parts = [f"{k}:{float(v):.2f}" for k, v in sc.items()]
    return " ".join(parts)


def _dayun_age_str(dayun: Dict[str, Any]) -> str:
    ymd = dayun.get("start_age_ymd")
    if not isinstance(ymd, dict):
        return "—"
    return (
        f"{ymd.get('years', 0)}y {ymd.get('months', 0)}m {ymd.get('days', 0)}d"
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True)
    p.add_argument("--birth", required=True)
    p.add_argument("--sex", choices=["M", "F"], required=True)
    p.add_argument("--calendar", choices=["solar", "lunar"], default="solar")
    p.add_argument("--years", type=int, default=24)
    p.add_argument("--out", default="report.html")
    args = p.parse_args()

    # 양력만 지원(음력 옵션은 향후 연동)
    naive = datetime.strptime(args.birth, "%Y-%m-%d %H:%M")
    birth_kst = KST.localize(naive)

    pillars = calc_four_pillars(birth_kst)
    dayun = calc_dayun(birth_kst, args.sex, pillars, count=8)
    flows: List[Dict[str, Any]] = build_yearly_flow(
        birth_kst, args.sex, pillars, dayun, span_years=args.years
    )
    summary = summarize_element_tendency(flows)
    r = summary["overall_ratio"]
    if not isinstance(r, dict):
        r = {k: 0.0 for k in _ELEMENTS}

    rows: List[str] = []
    for row in flows:
        es = row.get("element_score")
        if not isinstance(es, dict):
            es = {}
        strong = sorted(
            es.items(), key=lambda x: float(x[1]) if x[1] is not None else 0.0, reverse=True
        )[:2]
        strong_txt = "/".join([str(k) for k, v in strong if float(v or 0) > 0])
        du = row.get("dayun_pillar")
        yp = row.get("year_pillar")
        du_s = du.get("stem", "") if isinstance(du, dict) else ""
        du_b = du.get("branch", "") if isinstance(du, dict) else ""
        ys = yp.get("stem", "") if isinstance(yp, dict) else ""
        yb = yp.get("branch", "") if isinstance(yp, dict) else ""
        rows.append(
            f"<tr><td>{row.get('year', '')}</td>"
            f"<td>{du_s}{du_b}</td>"
            f"<td>{ys}{yb}</td>"
            f"<td>{strong_txt}</td>"
            f"<td>{_format_score_cell(es)}</td></tr>"
        )

    du_start = str(dayun.get("start_datetime_kst", "—"))

    html = TEMPLATE.format(
        name=args.name,
        birth=args.birth,
        sex=args.sex,
        calendar=args.calendar,
        r_m=_ratio_bar_pct(r, "木"),
        r_h=_ratio_bar_pct(r, "火"),
        r_t=_ratio_bar_pct(r, "土"),
        r_g=_ratio_bar_pct(r, "金"),
        r_s=_ratio_bar_pct(r, "水"),
        txt_m=_ratio_txt(r, "木"),
        txt_h=_ratio_txt(r, "火"),
        txt_t=_ratio_txt(r, "土"),
        txt_g=_ratio_txt(r, "金"),
        txt_s=_ratio_txt(r, "水"),
        note=summary.get("note", ""),
        du_dir=str(dayun.get("direction", "—")),
        du_start=du_start,
        du_age=_dayun_age_str(dayun),
        years=args.years,
        rows="\n".join(rows),
    )
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ HTML 저장: {os.path.abspath(args.out)}  (브라우저로 열어 'PDF로 저장' 가능)")


if __name__ == "__main__":
    main()
