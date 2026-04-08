# unteim/reports/main_report.py
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import sys

from .report_core import build_full_report


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="main_report",
        description="Unteim PDF Report CLI (main -> report_core only)",
    )

    # 필수
    parser.add_argument("--name", required=True, help="이름")
    parser.add_argument("--birth", required=True, help="생년월일시 (예: 1990-01-01 09:30)")
    parser.add_argument("--sex", required=True, choices=["M", "F"], help="성별 (M/F)")

    # 선택
    parser.add_argument(
        "--calendar",
        choices=["solar", "lunar"],
        default="solar",
        help="입력 달력 종류 (solar=양력 / lunar=음력)",
    )

    # 출력 제어(선택)
    parser.add_argument(
        "--out",
        default="report.pdf",
        help="출력 PDF 파일명(상대/절대 경로 모두 가능). 기본: report.pdf",
    )
    parser.add_argument(
        "--json",
        dest="print_json",
        action="store_true",
        help="PDF 생성 결과(메타/경로 등)를 JSON으로 stdout 출력",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="--json 출력 시 보기 좋게(indent) 출력",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    # ✅ main은 오직 report_core 진입점 1개만 호출
    # build_full_report()가 내부에서 엔진/섹션/스타일/어댑터를 모두 처리해야 함.
    result = build_full_report(
        name=args.name,
        birth=args.birth,
        sex=args.sex,
        calendar=args.calendar,
        out_path=args.out,
    )
    result["monthly_commentary"] = result.get("monthly_commentary", [])

    # 선택: JSON 출력
    if args.print_json:
        if args.pretty:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(result, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
