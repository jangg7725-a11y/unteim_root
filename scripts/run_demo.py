# unteim/scripts/run_demo.py
from __future__ import annotations

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict

# 내부 엔진
from engine.sajuCalculator import calculate_saju, _to_shinsal_pillars
from engine.oheng_analyzer import analyze_oheng
from engine.shinsal_detector import detect_shinsal
from engine.hidden_stems import hidden_elements_count_for_pillars
from engine.reporters import make_report
from engine.types import SajuPillars


def run_once(dt_text: str, strict: bool = False) -> Dict[str, Any]:
    """
    dt_text 예시: "1966-11-04 02:05"
    strict=True 이면 분석 단계에서 입력/무결성 엄격 검사
    """
    # 1) 사주 계산 (연/월/일/시의 간·지 산출; 내부에서 skyfield/절기 보정 등)
    saju: SajuPillars = calculate_saju(dt_text)

    # 2) 오행 분석 (천간+지지 8개 합산), 신살 탐지, 지장간 오행 집계
    oheng = analyze_oheng(saju, strict=strict)
    _sh = detect_shinsal(_to_shinsal_pillars(saju))
    shinsal = _sh["items"] if isinstance(_sh, dict) and "items" in _sh else _sh
    hidden_counts = hidden_elements_count_for_pillars(saju, strict=strict)

    # 3) 텍스트 리포트(지장간 오행 요약까지 포함)
    text = make_report({
        "saju": saju,
        "oheng": oheng,
        "shinsal": shinsal,
        "hidden_counts": hidden_counts,
        "meta": {
            "notes": [],
        },
    })

    out = {
        "input": dt_text,
        "saju": asdict(saju),
        "oheng": oheng,
        "shinsal": shinsal,
        "hidden_counts": hidden_counts,
        "text_report": text,
    }
    return out


def main() -> None:
    p = argparse.ArgumentParser(
        description="UNTEIM 엔드투엔드: 생년월일시 → 사주 → 오행/신살/지장간 오행 → 리포트"
    )
    p.add_argument("--dt", required=True, help='형식: "YYYY-MM-DD HH:MM" (예: "1966-11-04 02:05")')
    p.add_argument("--strict", action="store_true", help="엄격 모드(입력·무결성 오류 시 즉시 예외)")
    p.add_argument("--json-out", default="", help="JSON 결과 저장 경로(옵션). 예: out/demo_result.json")
    p.add_argument("--text-out", default="", help="텍스트 리포트 저장 경로(옵션). 예: out/demo_report.txt")
    p.add_argument("--print-json", action="store_true", help="콘솔에 JSON도 함께 출력")

    args = p.parse_args()

    result = run_once(args.dt, strict=args.strict)

    print("\n===== [UNTEIM 데모 리포트] =====")
    print(result["text_report"])

    if args.json_out:
        Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n[저장] JSON  → {args.json_out}")

    if args.text_out:
        Path(args.text_out).parent.mkdir(parents=True, exist_ok=True)
        with open(args.text_out, "w", encoding="utf-8") as f:
            f.write(result["text_report"].rstrip() + "\n")
        print(f"[저장] 리포트 → {args.text_out}")

    if args.print_json:
        print("\n----- JSON -----")
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
