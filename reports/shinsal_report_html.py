# -*- coding: utf-8 -*-
"""
신살 카드 리포트(HTML)
detect_shinsal() + explain_shinsal_items() 결과를 카드로 렌더링
실행 예)
  python -m reports.shinsal_report_html --out out/shinsal_report.html
  python -m reports.shinsal_report_html --name "오슈님" --age 43 --sex F --married --job public --out shinsal.html
"""
from __future__ import annotations
import argparse, os
from pathlib import Path
from typing import Dict, Any, List

from engine.shinsalDetector import detect_shinsal
from engine.shinsal_explainer import explain_shinsal_items

from engine.hidden_stems import (
    pillars_hidden_stems,
    count_stem_presence,
)


# 톤→색상(밝은 파스텔)
TONE_BG = {
    "positive": "linear-gradient(135deg,#fffde6,#fff8cc)",
    "neutral":  "linear-gradient(135deg,#f0f2f5,#e9edf3)",
    "caution":  "linear-gradient(135deg,#ffeaea,#ffdcdc)",
}
TONE_ICON = {"positive":"✨","neutral":"💡","caution":"⚠️"}

def _html_head(title: str) -> str:
    return f"""<!DOCTYPE html><html lang="ko"><head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>{title}</title>
<style>
  body{{font-family:"Segoe UI","맑은 고딕",sans-serif;background:#f5f6fa;margin:0;padding:24px}}
  .wrap{{max-width:1080px;margin:0 auto}}
  h1{{margin:8px 0 16px;font-size:26px}}
  .meta{{color:#555;margin-bottom:16px}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px}}
  .card{{border-radius:18px;box-shadow:0 6px 14px rgba(0,0,0,.08);padding:18px;min-height:220px;display:flex;flex-direction:column;justify-content:space-between}}
  .title{{font-weight:700;font-size:18px;margin-bottom:8px;display:flex;align-items:center;gap:8px}}
  .tone-badge{{font-size:12px;padding:2px 8px;border-radius:999px;background:rgba(0,0,0,.08)}}
  ul{{margin:8px 0 10px 16px;padding:0}}
  li{{margin:4px 0}}
  .advice{{margin-top:8px;padding-top:8px;border-top:1px dashed rgba(0,0,0,.15);font-size:14px;color:#333}}
  .flags{{margin-top:6px;display:flex;gap:6px;flex-wrap:wrap}}
  .flag{{font-size:12px;padding:2px 6px;border-radius:8px;background:rgba(0,0,0,.06)}}
  .footer{{margin-top:20px;color:#777;font-size:12px}}
</style></head><body><div class="wrap">"""

def _html_tail() -> str:
    return "</div></body></html>"

def _flag_label(k: str, v: Any) -> str:
    if isinstance(v, bool):
        if not v: return ""
        return {"love":"연애","job":"일","move":"이동","leadership":"리더십"}.get(k, k)
    if k == "luck": return "행운↑"
    if k == "brand": return "브랜드"
    if k == "risk":  return "리스크"
    if k == "impulse": return "충동"
    return str(k)

def render_cards_html(cards: List[Dict[str,Any]], title="신살 카드 리포트", meta: str = "") -> str:
    parts = [_html_head(title)]
    parts.append(f"<h1>{title}</h1>")
    if meta:
        parts.append(f'<div class="meta">{meta}</div>')
    parts.append('<div class="grid">')
    for c in cards:
        tone = c.get("tone","neutral")
        bg = TONE_BG.get(tone, TONE_BG["neutral"])
        icon = TONE_ICON.get(tone,"💡")
        flags = c.get("flags",{})
        flag_html = "".join(
            f'<span class="flag">{_flag_label(k,v)}</span>' for k,v in flags.items() if _flag_label(k,v)
        )
        bullets = "".join(f"<li>{b}</li>" for b in c.get("bullets",[]))
        parts.append(f"""
        <div class="card" style="background:{bg}">
          <div>
            <div class="title">{icon} {c.get("title","")} <span class="tone-badge">{tone}</span></div>
            <ul>{bullets}</ul>
          </div>
          <div class="advice">✦ {c.get("advice","")}</div>
          <div class="flags">{flag_html}</div>
        </div>""")
    parts.append("</div>")
    parts.append('<div class="footer">※ 본 해석은 입력하신 프로필(결혼유무/연령/직업군 등)에 따라 조건부로 달라집니다.</div>')
    parts.append(_html_tail())
    return "".join(parts)

def _render_hidden_stems_section(pillars: dict) -> str:
    """
    지장간 섹션 HTML 생성:
      - 각 기둥별 지장간 목록
      - 전체 가중치 합(내재 에너지 Top3)
    """
    hs = pillars_hidden_stems(pillars)           # {'year':[('丁',90),...], ...}
    agg = count_stem_presence(pillars)           # {'癸':120, '庚':70, ...}
    # 가중치 내림차순 상위 3개
    top = sorted(agg.items(), key=lambda x: x[1], reverse=True)[:3]

    def fmt_list(lst):
        if not lst:
            return "—"
        return ", ".join([f"{st}{pct}%" for st, pct in lst])

    rows = []
    rows.append(f"""
      <tr><th>연支</th><td>{fmt_list(hs.get('year', []))}</td></tr>
      <tr><th>월支</th><td>{fmt_list(hs.get('month', []))}</td></tr>
      <tr><th>일支</th><td>{fmt_list(hs.get('day', []))}</td></tr>
      <tr><th>시支</th><td>{fmt_list(hs.get('hour', []))}</td></tr>
    """)
    table_by_pillar = f"""
      <table class="hzg by-pillar">
        <thead><tr><th colspan="2">지장간 (각 기둥)</th></tr></thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
    """

    # 합산 표
    agg_rows = "\n".join(
        [f"<tr><td>{st}</td><td>{val}</td></tr>" for st, val in sorted(agg.items(), key=lambda x:x[1], reverse=True)]
    ) or "<tr><td colspan='2'>—</td></tr>"
    table_sum = f"""
      <table class="hzg summary">
        <thead><tr><th colspan="2">지장간 합산 가중치</th></tr></thead>
        <tbody>
          {agg_rows}
        </tbody>
      </table>
    """

    # Top3 뱃지
    top_badge = " · ".join([f"{st}{val}" for st, val in top]) or "—"
    badge_html = f"""
      <div class="hzg-top">
        <div class="chip">지장간 Top3: {top_badge}</div>
        <p class="hint">※ 지장간 합산은 ‘내재 에너지’ 경향을 빠르게 파악하는 지표입니다.</p>
      </div>
    """

    section = f"""
      <section id="hidden-stems" class="card">
        <h2>지장간 요약</h2>
        {badge_html}
        <div class="grid-2">
          {table_by_pillar}
          {table_sum}
        </div>
      </section>
    """
    return section

 
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="고객")
    ap.add_argument("--age", type=int, default=27)
    ap.add_argument("--sex", choices=["F","M"], default="F")
    ap.add_argument("--married", action="store_true")  # 체크되면 기혼
    ap.add_argument("--job", default="service")
    ap.add_argument("--out", default="shinsal_report.html")
    args = ap.parse_args()

    # 샘플: pillars는 실제 엔진의 값을 연결하세요.
    pillars = {"year":("丙","午"),"month":("庚","酉"),"day":("戊","申"),"hour":("癸","丑")}
    items = detect_shinsal(pillars)["items"]

    profile: Dict[str,Any] = {
        "marital_status": "married" if args.married else "single",
        "gender": args.sex,
        "age": args.age,
        "job_group": args.job
    }
    cards = explain_shinsal_items(items, profile)
    hidden_stems_html = _render_hidden_stems_section(pillars)
 

    meta = f"{args.name} · 성별 {args.sex} · 나이 {args.age}세 · 결혼 {'기혼' if args.married else '미혼'} · 직업 {args.job}"
    html = render_cards_html(cards, title="신살 카드 리포트", meta=meta)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"[OK] HTML 저장: {out.resolve()}")

if __name__ == "__main__":
    main()
