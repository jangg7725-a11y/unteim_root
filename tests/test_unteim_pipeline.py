# tests/test_unteim_pipeline.py
"""
UNTEIM 통합 파이프라인 테스트
- python -m pytest tests/test_unteim_pipeline.py -v
"""
from __future__ import annotations

from datetime import date, datetime

import pytest

import unteim
from engine.sajuCalculator import calculate_saju, analyze_saju


# ============================================================
# 1. 패키지 기본 검증
# ============================================================

class TestPackageBasic:
    """unteim 패키지 진입점이 정상인지 확인"""

    def test_version_exists(self):
        assert hasattr(unteim, "__version__")
        assert isinstance(unteim.__version__, str)

    def test_public_api_exists(self):
        for name in ("calculate_saju", "analyze_oheng", "detect_shinsal",
                      "get_solar_terms", "fetch_kasi_data"):
            assert hasattr(unteim, name), f"unteim.{name} 이 없습니다"


# ============================================================
# 2. 사주 기둥 계산 (calculate_saju)
# ============================================================

# 여러 생년월일로 테스트
BIRTH_SAMPLES = [
    "1966-11-04 02:05",
    "1990-01-01 09:30",
    "1988-08-15 14:10",
    "2000-02-04 00:30",
    "1975-12-25 23:50",
]


class TestCalculateSaju:
    """calculate_saju() 기본 구조 검증"""

    @pytest.mark.parametrize("birth", BIRTH_SAMPLES)
    def test_pillars_keys_exist(self, birth: str):
        result = unteim.calculate_saju(birth)
        for key in ("year", "month", "day", "hour"):
            assert key in result, f"'{key}' 키가 결과에 없습니다: {birth}"

    @pytest.mark.parametrize("birth", BIRTH_SAMPLES)
    def test_pillars_gan_ji_not_empty(self, birth: str):
        result = unteim.calculate_saju(birth)
        for key in ("year", "month", "day", "hour"):
            item = result[key]
            assert isinstance(item, dict), f"{key}가 dict가 아닙니다"
            assert item.get("gan"), f"{key}.gan 이 비어 있습니다: {birth}"
            assert item.get("ji"), f"{key}.ji 이 비어 있습니다: {birth}"

    def test_meta_exists(self):
        result = unteim.calculate_saju("1966-11-04 02:05")
        assert "meta" in result

    def test_known_result(self):
        """이미 확인된 결과와 비교"""
        result = unteim.calculate_saju("1966-11-04 02:05")
        assert result["year"]["gan"] == "丙"
        assert result["year"]["ji"] == "午"
        assert result["day"]["gan"] == "丁"
        assert result["day"]["ji"] == "卯"


# ============================================================
# 3. 엔진 전체 분석 (analyze_saju)
# ============================================================

class TestAnalyzeSaju:
    """analyze_saju() 전체 파이프라인 검증"""

    @pytest.fixture
    def result(self):
        return analyze_saju("1966-11-04 02:05")

    def test_top_keys(self, result):
        expected = {"birth_str", "pillars", "oheng", "shinsal", "wolwoon", "sewun", "daewoon"}
        assert expected.issubset(set(result.keys())), f"누락 키: {expected - set(result.keys())}"

    def test_pillars_structure(self, result):
        pillars = result["pillars"]
        assert "gan" in pillars
        assert "ji" in pillars
        assert len(pillars["gan"]) == 4
        assert len(pillars["ji"]) == 4

    def test_oheng_no_error(self, result):
        oheng = result["oheng"]
        assert isinstance(oheng, dict)
        assert "error" not in oheng, f"오행 분석 에러: {oheng.get('error')}"

    def test_oheng_has_counts(self, result):
        oheng = result["oheng"]
        if "counts" in oheng:
            counts = oheng["counts"]
            assert isinstance(counts, dict)
            assert len(counts) >= 1

    def test_shinsal_no_error(self, result):
        shinsal = result["shinsal"]
        assert isinstance(shinsal, dict)
        assert "error" not in shinsal, f"신살 분석 에러: {shinsal.get('error')}"

    def test_shinsal_has_items(self, result):
        shinsal = result["shinsal"]
        if "items" in shinsal:
            assert isinstance(shinsal["items"], list)
            assert len(shinsal["items"]) >= 1

    def test_wolwoon_is_list(self, result):
        assert isinstance(result["wolwoon"], list)

    def test_sewun_is_list(self, result):
        assert isinstance(result["sewun"], list)

    def test_daewoon_is_list(self, result):
        assert isinstance(result["daewoon"], list)
        assert len(result["daewoon"]) >= 1


# ============================================================
# 4. 대운 나이 정수 검증
# ============================================================

class TestDaewoonAge:
    """대운 start_age / end_age 가 정수인지 확인"""

    def test_ages_are_integers(self):
        result = analyze_saju("1966-11-04 02:05")
        for item in result["daewoon"]:
            assert isinstance(item["start_age"], int), \
                f"start_age가 int가 아닙니다: {item['start_age']}"
            assert isinstance(item["end_age"], int), \
                f"end_age가 int가 아닙니다: {item['end_age']}"

    def test_ages_increase(self):
        result = analyze_saju("1966-11-04 02:05")
        ages = [item["start_age"] for item in result["daewoon"]]
        for i in range(1, len(ages)):
            assert ages[i] > ages[i - 1], f"대운 나이가 증가하지 않음: {ages}"

    def test_pillar_not_empty(self):
        result = analyze_saju("1966-11-04 02:05")
        for item in result["daewoon"]:
            assert item["pillar"], "대운 간지가 비어 있습니다"
            assert len(item["pillar"]) == 2, f"대운 간지 길이 이상: {item['pillar']}"


# ============================================================
# 5. 절기 / KASI 데이터 검증
# ============================================================

class TestSolarTerms:
    """절기 데이터가 정상적으로 반환되는지 확인"""

    def test_solar_terms_2025(self):
        terms = unteim.get_solar_terms(date(2025, 2, 3))
        assert isinstance(terms, list)
        assert len(terms) >= 1

    def test_kasi_data_structure(self):
        data = unteim.fetch_kasi_data(date(2025, 2, 3))
        assert isinstance(data, dict)
        assert "solar_terms" in data

    def test_solar_terms_by_year(self):
        terms = unteim.get_solar_terms("2025")
        assert isinstance(terms, list)


# ============================================================
# 6. 여러 생년월일 일괄 검증
# ============================================================

class TestMultipleBirths:
    """다양한 생년월일로 엔진이 깨지지 않는지 확인"""

    @pytest.mark.parametrize("birth", BIRTH_SAMPLES)
    def test_analyze_saju_no_crash(self, birth: str):
        result = analyze_saju(birth)
        assert "pillars" in result
        assert "oheng" in result
        assert "shinsal" in result
        assert "daewoon" in result

    @pytest.mark.parametrize("birth", BIRTH_SAMPLES)
    def test_no_error_in_any_section(self, birth: str):
        result = analyze_saju(birth)
        for section in ("oheng", "shinsal"):
            data = result[section]
            if isinstance(data, dict):
                assert "error" not in data, \
                    f"{section} 에러 ({birth}): {data.get('error')}"


# ============================================================
# 7. 엔진 내부 타입 검증
# ============================================================

class TestEngineInternal:
    """엔진 내부 calculate_saju()가 SajuPillars 객체를 반환하는지 확인"""

    def test_returns_saju_pillars_type(self):
        pillars = calculate_saju("1966-11-04 02:05")
        assert hasattr(pillars, "gan")
        assert hasattr(pillars, "ji")
        assert len(pillars.gan) == 4
        assert len(pillars.ji) == 4

    def test_as_dict_method(self):
        pillars = calculate_saju("1966-11-04 02:05")
        if hasattr(pillars, "as_dict"):
            d = pillars.as_dict()
            assert isinstance(d, dict)
            for key in ("year", "month", "day", "hour"):
                assert key in d

    def test_meta_has_month_term(self):
        pillars = calculate_saju("1966-11-04 02:05")
        meta = getattr(pillars, "meta", {}) or {}
        assert "month_term" in meta, "meta에 month_term이 없습니다"
