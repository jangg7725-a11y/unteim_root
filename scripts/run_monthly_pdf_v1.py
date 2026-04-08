import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from engine.sajuCalculator import calculate_saju
from engine.full_analyzer import analyze_full
from engine.monthly_patterns_v1_1 import attach_month_patterns_v1_1
from engine.types import SajuPillars
from reports.report_core import build_pdf_report


def main():
    name = "장경옥"
    birth = "1966-11-04 02:00"
    sex = "여자"

    saju: SajuPillars = calculate_saju(birth)
    report = analyze_full(saju.as_dict(), birth_str=birth)

    report.setdefault("profile", {})
    report["profile"]["name"] = name
    report["profile"]["sex"] = sex

    report = attach_month_patterns_v1_1(report)

    out = Path("out") / "monthly_report.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)

    build_pdf_report(report, out_path=str(out))
    print("PDF OK ->", out)

if __name__ == "__main__":
    main()
