from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

# 👉 report_core 안에 정의된 함수 import
from reports.report_core import (
    _append_monthly_summary_boxes,
)

def run_test():
    pdf_path = "out/test_monthly_summary_box.pdf"

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    story = []

    # ✅ 가짜 월간 리포트 데이터 (1개만)
    monthly_reports = [
        {
            "meta": {
                "year": 2026,
                "month": 3,
            }
        }
    ]

    # 🔑 핵심: 요약 박스 컨트롤러 호출
    _append_monthly_summary_boxes(
        story,
        styles,
        monthly_reports
    )

    doc.build(story)
    print(f"PDF 생성 완료: {pdf_path}")

if __name__ == "__main__":
    run_test()
