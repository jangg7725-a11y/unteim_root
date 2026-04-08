# unteim/tests/test_reports.py

from engine.reporters import make_report

def test_make_report_smoke():
    """
    리포트 출력이 최소한 동작하는지 확인하는 스모크 테스트.
    """
    dummy_saju = {
        "gan": ["병", "경", "무", "계"],
        "ji": ["오", "자", "신", "축"],
    }
    result = make_report(dummy_saju)

    # 최소한 결과가 문자열이어야 함
    assert isinstance(result, str)
    assert "천간" in result
    assert "지지" in result
