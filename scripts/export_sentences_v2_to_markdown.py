#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Export data/sentence_archive/sentences_v2.json to human-readable Markdown (reader companion)."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JSON_PATH = ROOT / "data" / "sentence_archive" / "sentences_v2.json"
OUT_PATH = ROOT / "data" / "sentences_v2_reader.md"

# Manuscript-aligned tips (not stored as separate sentences in JSON)
TIPS = {
    "A": (
        "오행 분석 결과나 성격 요약 페이지에 삽입하세요. "
        "단순히 '성격이 이렇다'가 아니라, '왜 그런 행동 패턴이 나타났는지' 공감하며 설명해 줍니다."
    ),
    "B": (
        "용신(나에게 필요한 기운) 결과 탭이나, 월간/연간 운세 솔루션 부분에 구체적인 액션 플랜으로 제공하세요. "
        "작은 실천이 마음의 환기를 돕습니다."
    ),
    "C": (
        "리포트의 서문(도입부)과 맺음말에 배치하여, 사용자가 리포트를 열 때와 닫을 때 "
        "'따뜻한 위로와 긍정적인 힘'을 받을 수 있도록 합니다."
    ),
}

PHILOSOPHY_LONG = (
    "이 문장들은 운명을 규정하는 것이 아닙니다. 사용자가 자신의 삶의 패턴을 이해하고, "
    "스스로 더 밝고 긍정적인 방향으로 나아갈 수 있도록 돕는 '자기이해의 나침반' 역할을 합니다. "
    "모든 문장에는 위로, 자기 긍정, 그리고 용기가 담겨 있습니다."
)

_DUP_COLON_PREFIX = re.compile(r"^([^:]+):\1:\s*")


def md_escape_cell(s: str) -> str:
    return s.replace("|", "\\|")


def dedupe_subsection(s: str) -> str:
    if not s:
        return s
    n = len(s)
    if n % 2 == 0 and n >= 4:
        mid = n // 2
        if s[:mid] == s[mid:]:
            return s[:mid]
    return s


def normalize_sentence_text(text: str) -> str:
    """Remove duplicate 'X:X:' prefixes introduced by data glitches."""
    t = text.strip()
    while True:
        m = _DUP_COLON_PREFIX.match(t)
        if not m:
            break
        t = m.group(1) + ": " + t[m.end() :].lstrip()
    return t


def oheng_table_to_md(rows: list[dict]) -> str:
    if not rows:
        return ""
    cols = list(rows[0].keys())
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    lines = [header, sep]
    for row in rows:
        lines.append(
            "| " + " | ".join(md_escape_cell(str(row.get(c, ""))) for c in cols) + " |"
        )
    return "\n".join(lines)


def render_section_sentences(section_title: str, sentences: list[dict]) -> str:
    lines: list[str] = [f"### {section_title}", ""]
    if not sentences:
        return "\n".join(lines)

    prev_sub: str | None = None
    prev_cond: str | None = None
    for item in sentences:
        ss = dedupe_subsection(item.get("subsection") or "")
        cc = (item.get("condition") or "").strip()
        text = normalize_sentence_text(item.get("text") or "")

        if ss and ss != prev_sub:
            lines.append(f"#### {ss}")
            lines.append("")
            prev_sub = ss
            prev_cond = None

        if cc and cc != prev_cond:
            lines.append(f"**[{cc}]**")
            lines.append("")
            prev_cond = cc

        lines.append(text)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    parts = data.get("parts", {})
    out: list[str] = []

    title = data.get("title", "UNTEIM 사주 리포트")
    version = data.get("version", "")
    out.append(f"# {title}")
    if version:
        out.append(f"## 버전 {version}")
    out.append("")
    out.append("### 💡 철학 및 비전 가이드")
    out.append("")
    out.append(PHILOSOPHY_LONG)
    out.append("")
    tag = data.get("philosophy", "")
    if tag:
        out.append(f"*({tag})*")
        out.append("")
    out.append("---")
    out.append("")

    # PART A
    pa = parts.get("A", {})
    out.append(f"## 🧭 PART A: {pa.get('title', '')}")
    out.append("")
    out.append("### 📋 리포트 활용 팁 (A 파트)")
    out.append("")
    out.append(TIPS["A"])
    out.append("")
    secs_a = pa.get("sections", {})
    for key in sorted(secs_a.keys()):
        sec = secs_a[key]
        st_title = sec.get("title", key)
        sents = sec.get("sentences", [])
        out.append(render_section_sentences(st_title, sents))
        out.append("---")
        out.append("")

    # PART B
    pb = parts.get("B", {})
    out.append(f"## 🛠️ PART B: {pb.get('title', '')}")
    out.append("")
    out.append("### 📋 리포트 활용 팁 (B 파트)")
    out.append("")
    out.append(TIPS["B"])
    out.append("")

    out.append("### 🎨 B-1. 오행별 실천 개운법 표")
    out.append("")
    table = pb.get("oheng_table", [])
    out.append(oheng_table_to_md(table))
    out.append("")
    out.append("---")
    out.append("")

    secs_b = pb.get("sections", {})
    order_b = ["B-2", "B-3", "B-4", "B-5"]
    for key in order_b:
        if key not in secs_b:
            continue
        sec = secs_b[key]
        st_title = sec.get("title", key)
        sents = sec.get("sentences", [])
        out.append(render_section_sentences(st_title, sents))
        out.append("---")
        out.append("")

    # PART C
    pc = parts.get("C", {})
    out.append(f"## 💌 PART C: {pc.get('title', '')}")
    out.append("")
    out.append("### 📋 리포트 활용 팁 (C 파트)")
    out.append("")
    out.append(TIPS["C"])
    out.append("")
    secs_c = pc.get("sections", {})
    for key in sorted(secs_c.keys()):
        sec = secs_c[key]
        st_title = sec.get("title", key)
        sents = sec.get("sentences", [])
        out.append(render_section_sentences(st_title, sents))
        out.append("---")
        out.append("")

    rel = JSON_PATH.relative_to(ROOT)
    total = data.get("total_sentences", "?")
    body = "\n".join(out).rstrip()
    body = re.sub(r"\n---\s*$", "", body)
    footer = (
        f"\n\n---\n\n*Generated from `{rel}` ({total} sentences). "
        f"Regenerate: `python scripts/export_sentences_v2_to_markdown.py`*\n"
    )
    text = body + footer

    OUT_PATH.write_text(text, encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
