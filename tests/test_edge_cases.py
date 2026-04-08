# tests/test_edge_cases.py
"""
UNTEIM 명식 정확도 검증 – 엣지 케이스
- python -m pytest unteim/tests/test_edge_cases.py -v
"""
from __future__ import annotations

import pytest

from engine.sajuCalculator import calculate_saju, analyze_saju


HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


# ============================================================
# 1. 입춘 경계 테스트
# ============================================================

class TestIpchunBoundary:
    """
    입춘 전후로 연주가 올바르게 바뀌는지 확인.

    예시 (2026년 입춘 = 2026-02-04 05:02:07 KST):
    - 2026-02-04 04:00 → 입춘 전 → 연주는 2025년 기준 (乙巳)
    - 2026-02-04 06:00 → 입춘 후 → 연주는 2026년 기준 (丙午)
    """

    def test_before_ipchun_2026(self):
        """2026년 입춘 전 → 연주가 乙巳(2025년)"""
        pillars = calculate_saju("2026-02-04 04:00")
        year_gan = pillars.gan[0]
        year_ji = pillars.ji[0]
        assert year_gan == "乙", f"입춘 전 연간이 乙이 아님: {year_gan}"
        assert year_ji == "巳", f"입춘 전 연지가 巳가 아님: {year_ji}"

    def test_after_ipchun_2026(self):
        """2026년 입춘 후 → 연주가 丙午(2026년)"""
        pillars = calculate_saju("2026-02-04 06:00")
        year_gan = pillars.gan[0]
        year_ji = pillars.ji[0]
        assert year_gan == "丙", f"입춘 후 연간이 丙이 아님: {year_gan}"
        assert year_ji == "午", f"입춘 후 연지가 午가 아님: {year_ji}"

    def test_before_ipchun_1990(self):
        """1990년 입춘(02-04 11:13:59 KST) 전 → 연주는 1989년(己巳)"""
        pillars = calculate_saju("1990-02-04 10:00")
        year_gan = pillars.gan[0]
        year_ji = pillars.ji[0]
        assert year_gan == "己", f"1990 입춘 전 연간이 己가 아님: {year_gan}"
        assert year_ji == "巳", f"1990 입춘 전 연지가 巳가 아님: {year_ji}"

    def test_after_ipchun_1990(self):
        """1990년 입춘 후 → 연주는 1990년(庚午)"""
        pillars = calculate_saju("1990-02-04 12:00")
        year_gan = pillars.gan[0]
        year_ji = pillars.ji[0]
        assert year_gan == "庚", f"1990 입춘 후 연간이 庚이 아님: {year_gan}"
        assert year_ji == "午", f"1990 입춘 후 연지가 午가 아님: {year_ji}"

    def test_year_changes_only_at_ipchun(self):
        """1월 1일생은 입춘 전이므로 전년도 연주를 써야 함"""
        pillars = calculate_saju("2026-01-15 12:00")
        year_gan = pillars.gan[0]
        year_ji = pillars.ji[0]
        assert year_gan == "乙", f"1월생 연간이 乙이 아님: {year_gan}"
        assert year_ji == "巳", f"1월생 연지가 巳가 아님: {year_ji}"


# ============================================================
# 2. 야자시 (23:00~00:59) 테스트
# ============================================================

class TestMidnightHour:
    """
    23:00~00:59 는 子시(0번째 지지).
    시주의 지지가 子인지 확인.
    """

    def test_2300_is_ja_si(self):
        """23:00 출생 → 시지 = 子"""
        pillars = calculate_saju("1990-06-15 23:00")
        hour_ji = pillars.ji[3]
        assert hour_ji == "子", f"23:00 시지가 子가 아님: {hour_ji}"

    def test_2330_is_ja_si(self):
        """23:30 출생 → 시지 = 子"""
        pillars = calculate_saju("1990-06-15 23:30")
        hour_ji = pillars.ji[3]
        assert hour_ji == "子", f"23:30 시지가 子가 아님: {hour_ji}"

    def test_0030_is_ja_si(self):
        """00:30 출생 → 시지 = 子"""
        pillars = calculate_saju("1990-06-16 00:30")
        hour_ji = pillars.ji[3]
        assert hour_ji == "子", f"00:30 시지가 子가 아님: {hour_ji}"

    def test_0100_is_chuk_si(self):
        """01:00 출생 → 시지 = 丑 (子시가 아님)"""
        pillars = calculate_saju("1990-06-16 01:00")
        hour_ji = pillars.ji[3]
        assert hour_ji == "丑", f"01:00 시지가 丑이 아님: {hour_ji}"

    def test_each_hour_branch(self):
        """모든 시간대의 시지가 올바른 지지를 반환하는지 확인"""
        expected = [
            (23, "子"), (0, "子"),
            (1, "丑"), (2, "丑"),
            (3, "寅"), (4, "寅"),
            (5, "卯"), (6, "卯"),
            (7, "辰"), (8, "辰"),
            (9, "巳"), (10, "巳"),
            (11, "午"), (12, "午"),
            (13, "未"), (14, "未"),
            (15, "申"), (16, "申"),
            (17, "酉"), (18, "酉"),
            (19, "戌"), (20, "戌"),
            (21, "亥"), (22, "亥"),
        ]
        for hour, expected_ji in expected:
            birth = f"1990-06-15 {hour:02d}:00"
            pillars = calculate_saju(birth)
            actual_ji = pillars.ji[3]
            assert actual_ji == expected_ji, \
                f"{hour}시 시지: 기대={expected_ji}, 실제={actual_ji}"


# ============================================================
# 3. 사주 기둥 구조 무결성 테스트
# ============================================================

class TestPillarIntegrity:
    """사주 기둥 값이 항상 유효한 천간/지지 문자인지 확인"""

    BIRTHS = [
        "1930-03-15 08:00",
        "1950-07-20 14:30",
        "1966-11-04 02:05",
        "1980-01-01 00:00",
        "1990-02-04 10:00",
        "2000-12-31 23:59",
        "2025-06-15 12:00",
        "2040-09-01 06:30",
    ]

    @pytest.mark.parametrize("birth", BIRTHS)
    def test_gan_values_are_valid(self, birth: str):
        pillars = calculate_saju(birth)
        for i, g in enumerate(pillars.gan):
            assert g in HEAVENLY_STEMS, \
                f"유효하지 않은 천간: pillars.gan[{i}]={g!r} ({birth})"

    @pytest.mark.parametrize("birth", BIRTHS)
    def test_ji_values_are_valid(self, birth: str):
        pillars = calculate_saju(birth)
        for i, j in enumerate(pillars.ji):
            assert j in EARTHLY_BRANCHES, \
                f"유효하지 않은 지지: pillars.ji[{i}]={j!r} ({birth})"


# ============================================================
# 4. 전체 분석 엣지 케이스 검증
# ============================================================

class TestAnalyzeEdgeCases:
    """다양한 경계값에서 analyze_saju가 깨지지 않는지 확인"""

    EDGE_BIRTHS = [
        "1966-02-04 15:00",   # 입춘 직전
        "1966-02-04 16:00",   # 입춘 직후
        "2000-02-04 21:00",   # 2000년 입춘 직전
        "2000-02-04 22:00",   # 2000년 입춘 직후
        "1990-06-15 23:30",   # 야자시
        "1990-06-16 00:15",   # 자정 직후
        "1975-12-31 23:59",   # 연말 야자시
        "1976-01-01 00:01",   # 신년 자정
    ]

    @pytest.mark.parametrize("birth", EDGE_BIRTHS)
    def test_no_crash(self, birth: str):
        result = analyze_saju(birth)
        assert "pillars" in result
        assert "oheng" in result
        assert "daewoon" in result

    @pytest.mark.parametrize("birth", EDGE_BIRTHS)
    def test_no_error_in_sections(self, birth: str):
        result = analyze_saju(birth)
        for section in ("oheng", "shinsal"):
            data = result[section]
            if isinstance(data, dict):
                assert "error" not in data, \
                    f"{section} 에러 ({birth}): {data.get('error')}"


# ============================================================
# 5. 일주 앵커 정합성 테스트
# ============================================================

class TestDayPillarAnchor:
    """
    일주 계산의 앵커(1984-02-02 = 甲子)가 맞는지 확인.
    """

    def test_anchor_date_is_jiazi(self):
        """1984-02-02 12:00 → 일주가 甲子"""
        pillars = calculate_saju("1984-02-02 12:00")
        assert pillars.gan[2] == "甲", f"앵커 일간이 甲이 아님: {pillars.gan[2]}"
        assert pillars.ji[2] == "子", f"앵커 일지가 子가 아님: {pillars.ji[2]}"

    def test_next_day_is_eulchuk(self):
        """1984-02-03 12:00 → 일주가 乙丑"""
        pillars = calculate_saju("1984-02-03 12:00")
        assert pillars.gan[2] == "乙", f"앵커+1일 일간이 乙이 아님: {pillars.gan[2]}"
        assert pillars.ji[2] == "丑", f"앵커+1일 일지가 丑이 아님: {pillars.ji[2]}"

    def test_60_days_later_is_jiazi_again(self):
        """1984-02-02 + 60일 = 1984-04-02 → 일주가 다시 甲子"""
        pillars = calculate_saju("1984-04-02 12:00")
        assert pillars.gan[2] == "甲", f"60일 후 일간이 甲이 아님: {pillars.gan[2]}"
        assert pillars.ji[2] == "子", f"60일 후 일지가 子가 아님: {pillars.ji[2]}"
