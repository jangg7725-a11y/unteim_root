# -*- coding: utf-8 -*-
"""
단일 birth 문자열로 full_analyzer → dict → report_core / monthly_report PDF 검증.
실행: 프로젝트 루트에서
  .venv\\Scripts\\python.exe scripts/verify_birth_pipeline.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

UNIFIED_KEYS = (
    "input",
    "pillars",
    "oheng",
    "geukguk",
    "sibsin",
    "yongshin",
    "daewun",
    "sewun",
    "monthly_flow",
    "sinsal",
    "twelve_states",
    "gongmang",
    "summary",
)


def main() -> int:
    birth = "1990-05-15 14:30"

    from engine.sajuCalculator import calculate_saju
    from engine.full_analyzer import analyze_full

    saju = calculate_saju(birth)
    pillars = saju.as_dict()
    packed = analyze_full(pillars, birth_str=birth)

    assert isinstance(packed, dict), "analyze_full must return dict"
    uni = packed.get("unified")
    assert isinstance(uni, dict), "packed['unified'] missing"
    missing = [k for k in UNIFIED_KEYS if k not in uni]
    assert not missing, f"unified keys missing: {missing}"

    out_dir = ROOT / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    js = out_dir / "verify_unified.json"
    js.write_text(
        json.dumps({"birth": birth, "unified_keys": list(uni.keys()), "unified": uni}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] unified schema: {len(UNIFIED_KEYS)} keys")
    print(f"[OK] wrote {js}")

    from reports.report_core import build_pdf_report

    pdf1 = out_dir / "verify_report_core.pdf"
    p1 = build_pdf_report(report=packed, out_path=str(pdf1))
    print(f"[OK] report_core PDF -> {p1}")

    from reports.monthly_report import build_monthly_report_pdf

    pdf2 = out_dir / "verify_monthly_report.pdf"
    p2 = build_monthly_report_pdf(report=packed, out_path=str(pdf2))
    print(f"[OK] monthly_report PDF -> {p2}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
