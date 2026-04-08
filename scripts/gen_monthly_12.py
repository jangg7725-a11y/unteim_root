from __future__ import annotations

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from zoneinfo import ZoneInfo
import inspect
from reports.monthly_report import build_monthly_report_pdf
from engine.sajuCalculator import calculate_saju
from engine.full_analyzer import analyze_full
from engine.month_commentary import build_month_commentary
# ✅ 프로젝트 내부 유틸
from engine.utils.filename_rules import MonthlyFilenameSpec, ensure_out_dir, monthly_pdf_name

# ✅ 여기만 “실제 월간 PDF 생성 함수”로 연결하면 끝
# 아래 import 경로/함수명은 프로젝트 현재 구성에 맞게 바꾸세요.
#
# 예시 A) 월간 PDF 생성 함수가 reports 쪽에 있을 때:
# from reports.monthly_pdf import build_monthly_pdf
#
# 예시 B) full_analyzer 결과를 받아 report_core가 PDF를 뽑을 때:
# from reports.report_core import render_monthly_pdf
#
# -----
# 여기서는 “함수 시그니처”만 가정해 둡니다.
def _call_with_supported_kwargs(fn, **candidates):
    """
    fn이 실제로 받는 파라미터만 골라서 호출 (시그니처 변화에 강함)
    """
    sig = inspect.signature(fn)
    params = set(sig.parameters.keys())
    kwargs = {k: v for k, v in candidates.items() if k in params}
    return fn(**kwargs)


def build_monthly_pdf(*, birth_str: str, year: int, month: int, out_path: Path, verbosity: str) -> None:
    # 1) pillars 계산
    pillars = calculate_saju(birth_str)

    # 2) analyze_full 호출 (year/month를 직접 넣지 말고, 가능한 형태로만 전달)
    when_payload = {
        "target_year": year,
        "target_month": month,
        "year": year,
        "month": month,
    }

    report = _call_with_supported_kwargs(
        analyze_full,   
        pillars=pillars,
        birth_str=birth_str,
        verbosity=verbosity,
        when=when_payload,          # analyze_full이 when을 받으면 사용
        target_year=year,           # 또는 이런 형태를 받으면 사용
        target_month=month,
        year=year,                  # (하지만 analyze_full이 안 받으면 자동 제외됨)
        month=month,
    )
    # ✅ 월간 리포트 메타 정보(표지용)
    if isinstance(report, dict):
        meta = report.setdefault("meta", {})
        meta["report_kind"] = "monthly"
        meta["year"] = year
        meta["month"] = month    
        
    # 3) report가 dict가 아닐 경우 방어
    if not isinstance(report, dict):
        report = {"report": report}

    # 4) 월간 코멘터리가 없으면 engine에서 보강 생성
    #    (monthly_report 쪽이 이 키를 참조할 가능성이 큼)
    

    # 5) when 정보도 최소로 고정
    when = report.get("when") or {}
    if isinstance(when, dict):
        when.setdefault("target_year", year)
        when.setdefault("target_month", month)
    report["when"] = when

    # 6) 월간 PDF 생성 (필수: report=)
    _call_with_supported_kwargs(
        build_monthly_report_pdf,
        report=report,
        out_path=str(out_path),
        pdf_path=str(out_path),
        output_path=str(out_path),
    )


@dataclass(frozen=True)
class Args:
    birth: str
    year: int
    tz: str
    out_dir: str
    verbosity: str


def parse_args() -> Args:
    p = argparse.ArgumentParser()
    p.add_argument("--birth", required=True, help="예: '1990-01-01 09:30'")
    p.add_argument("--year", type=int, required=True, help="예: 2026")
    p.add_argument("--tz", default="Asia/Seoul", help="기본 Asia/Seoul")
    p.add_argument("--out-dir", default="out", help="기본 out")
    p.add_argument("--verbosity", default="standard", choices=["short", "standard", "long"])
    a = p.parse_args()
    return Args(
        birth=a.birth,
        year=a.year,
        tz=a.tz,
        out_dir=a.out_dir,
        verbosity=a.verbosity,
    )


def main() -> int:
    args = parse_args()

    tz = ZoneInfo(args.tz)
    birth_dt = datetime.strptime(args.birth, "%Y-%m-%d %H:%M").replace(tzinfo=tz)

    out_dir = ensure_out_dir(args.out_dir)
    spec = MonthlyFilenameSpec(prefix="monthly", ext="pdf")

    for m in range(1, 13):
        fname = monthly_pdf_name(spec, args.year, m, birth_dt)
        out_path = out_dir / fname

        build_monthly_pdf(
            birth_str=args.birth,
            year=args.year,
            month=m,
            out_path=out_path,
            verbosity=args.verbosity,
        )
        print(f"[OK] {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
