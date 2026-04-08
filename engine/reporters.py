# unteim/engine/reporters.py
from __future__ import annotations
from typing import List, Dict, Any

# ── 내부 포맷 힌트:
# oheng: {"counts":{목/화/토/금/수}, "tips":[...], "summary":"..."}
# shinsal: [{"name":"반복지지","pillar":"연·일"}, ...]
# hidden_counts: {"木": float, "火": float, "土": float, "金": float, "水": float}

def _fmt_counts_line(counts: Dict[str, float]) -> str:
    # 오행 출력 순서를 고정(가독성)
    return f"목:{counts.get('木',0)}  화:{counts.get('火',0)}  토:{counts.get('土',0)}  금:{counts.get('金',0)}  수:{counts.get('水',0)}"

def format_oheng_report(oh: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("[오행 분석(천간/지지 합산)]")
    cnt = oh.get("counts", {})
    tip = oh.get("tips", [])
    lines.append(_fmt_counts_line(cnt))
    if tip:
        lines.append(" · ".join(tip))
    if "summary" in oh:
        lines.append(f"요약: {oh['summary']}")
    return "\n".join(lines)

def _shinsal_summary(shinsal: List[Dict[str, str]]) -> str:
    if not shinsal:
        return ""
    parts = [f"{h.get('name','')}({h.get('pillar','')})" for h in shinsal]
    return " · ".join(parts)

def format_shinsal_report(shinsal: List[Dict[str, str]]) -> str:
    if not shinsal:
        return "[신살] 해당 없음"
    return "[신살] " + _shinsal_summary(shinsal)

def format_hidden_counts(hidden_counts: Dict[str, float]) -> str:
    lines: List[str] = []
    lines.append("[지장간 오행 요약]")
    lines.append(_fmt_counts_line(hidden_counts))
    return "\n".join(lines)

def make_report(bundle: Dict[str, Any]) -> str:
    """
    통합 텍스트 리포트 작성.
    bundle = {
      "saju": {...},
      "oheng": {...},
      "shinsal": [...],
      "hidden_counts": {...},
      "meta": {"notes":[...]}
    }
    """
    lines: List[str] = []
    lines.append("===== [사주 리포트] =====")

    # 1) 오행(천간/지지)
    oh = bundle.get("oheng", {})
    lines.append(format_oheng_report(oh))

    # 2) 지장간 오행
    hc = bundle.get("hidden_counts", {})
    if hc:
        lines.append(format_hidden_counts(hc))

    # 3) 신살
    sh = bundle.get("shinsal", [])
    lines.append(format_shinsal_report(sh))

    # 4) 메모
    meta = bundle.get("meta", {})
    notes = meta.get("notes", [])
    if notes:
        lines.append("\n[해석 메모]")
        for n in notes:
            lines.append(f" - {n}")
    return "\n".join(lines)
