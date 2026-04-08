# tests/test_output_schema.py
"""
UNTEIM JSON 스키마 검증 테스트
- python -m pytest unteim/tests/test_output_schema.py -v
"""
from __future__ import annotations

import pytest

from engine.sajuCalculator import analyze_saju
from engine.output_schema import (
    SCHEMA_VERSION,
    REQUIRED_TOP_KEYS,
    PILLARS_REQUIRED_KEYS,
    OHENG_REQUIRED_KEYS,
    OHENG_ELEMENT_NAMES,
    SHINSAL_ITEM_KEYS,
    SHINSAL_SUMMARY_KEYS,
    WOLWOON_ITEM_KEYS,
    SEWUN_ITEM_KEYS,
    DAEWOON_ITEM_KEYS,
)

BIRTH = "1966-11-04 02:05"


@pytest.fixture
def result():
    return analyze_saju(BIRTH)


# ============================================================
# 1. 스키마 버전 확인
# ============================================================

class TestSchemaVersion:
    def test_version_exists(self):
        assert SCHEMA_VERSION
        assert isinstance(SCHEMA_VERSION, str)


# ============================================================
# 2. 최상위 키 검증
# ============================================================

class TestTopKeys:
    def test_all_required_keys_exist(self, result):
        for key in REQUIRED_TOP_KEYS:
            assert key in result, f"최상위 키 '{key}'가 없습니다"

    def test_birth_str_is_string(self, result):
        assert isinstance(result["birth_str"], str)
        assert len(result["birth_str"]) >= 10


# ============================================================
# 3. pillars 스키마 검증
# ============================================================

class TestPillarsSchema:
    def test_pillars_keys(self, result):
        pillars = result["pillars"]
        for key in PILLARS_REQUIRED_KEYS:
            assert key in pillars, f"pillars에 '{key}'가 없습니다"

    def test_gan_is_list_of_4_strings(self, result):
        gan = result["pillars"]["gan"]
        assert isinstance(gan, list)
        assert len(gan) == 4
        for g in gan:
            assert isinstance(g, str) and len(g) == 1

    def test_ji_is_list_of_4_strings(self, result):
        ji = result["pillars"]["ji"]
        assert isinstance(ji, list)
        assert len(ji) == 4
        for j in ji:
            assert isinstance(j, str) and len(j) == 1

    def test_meta_is_dict(self, result):
        meta = result["pillars"]["meta"]
        assert isinstance(meta, dict)


# ============================================================
# 4. oheng 스키마 검증
# ============================================================

class TestOhengSchema:
    def test_oheng_keys(self, result):
        oheng = result["oheng"]
        assert isinstance(oheng, dict)
        for key in OHENG_REQUIRED_KEYS:
            assert key in oheng, f"oheng에 '{key}'가 없습니다"

    def test_counts_has_five_elements(self, result):
        counts = result["oheng"].get("counts", {})
        for elem in OHENG_ELEMENT_NAMES:
            assert elem in counts, f"oheng.counts에 '{elem}'이 없습니다"
            assert isinstance(counts[elem], int)

    def test_summary_is_string(self, result):
        assert isinstance(result["oheng"]["summary"], str)


# ============================================================
# 5. shinsal 스키마 검증
# ============================================================

class TestShinsalSchema:
    def test_shinsal_is_dict(self, result):
        assert isinstance(result["shinsal"], dict)

    def test_no_error(self, result):
        assert "error" not in result["shinsal"], \
            f"shinsal 에러: {result['shinsal'].get('error')}"

    def test_items_structure(self, result):
        items = result["shinsal"].get("items", [])
        assert isinstance(items, list)
        for item in items:
            for key in SHINSAL_ITEM_KEYS:
                assert key in item, f"shinsal item에 '{key}'가 없습니다"

    def test_summary_structure(self, result):
        summary = result["shinsal"].get("summary", {})
        if summary:
            for key in SHINSAL_SUMMARY_KEYS:
                assert key in summary, f"shinsal summary에 '{key}'가 없습니다"


# ============================================================
# 6. wolwoon 스키마 검증
# ============================================================

class TestWolwoonSchema:
    def test_wolwoon_is_list(self, result):
        assert isinstance(result["wolwoon"], list)

    def test_item_keys(self, result):
        for item in result["wolwoon"]:
            for key in WOLWOON_ITEM_KEYS:
                assert key in item, f"wolwoon item에 '{key}'가 없습니다"


# ============================================================
# 7. sewun 스키마 검증
# ============================================================

class TestSewunSchema:
    def test_sewun_is_list(self, result):
        assert isinstance(result["sewun"], list)
        assert len(result["sewun"]) >= 1

    def test_item_keys(self, result):
        for item in result["sewun"]:
            for key in SEWUN_ITEM_KEYS:
                assert key in item, f"sewun item에 '{key}'가 없습니다"

    def test_year_is_int(self, result):
        for item in result["sewun"]:
            assert isinstance(item["year"], int)


# ============================================================
# 8. daewoon 스키마 검증
# ============================================================

class TestDaewoonSchema:
    def test_daewoon_is_list(self, result):
        assert isinstance(result["daewoon"], list)
        assert len(result["daewoon"]) >= 1

    def test_item_keys(self, result):
        for item in result["daewoon"]:
            for key in DAEWOON_ITEM_KEYS:
                assert key in item, f"daewoon item에 '{key}'가 없습니다"

    def test_ages_are_int(self, result):
        for item in result["daewoon"]:
            assert isinstance(item["start_age"], int)
            assert isinstance(item["end_age"], int)

    def test_pillar_is_two_chars(self, result):
        for item in result["daewoon"]:
            assert isinstance(item["pillar"], str)
            assert len(item["pillar"]) == 2


# ============================================================
# 9. 여러 생년월일로 스키마 일관성 검증
# ============================================================

BIRTHS = [
    "1966-11-04 02:05",
    "1990-01-01 09:30",
    "2000-02-04 22:00",
    "2025-06-15 12:00",
]

class TestSchemaConsistency:
    @pytest.mark.parametrize("birth", BIRTHS)
    def test_top_keys_always_present(self, birth):
        result = analyze_saju(birth)
        for key in REQUIRED_TOP_KEYS:
            assert key in result, f"'{key}' 누락 ({birth})"

    @pytest.mark.parametrize("birth", BIRTHS)
    def test_pillars_always_4(self, birth):
        result = analyze_saju(birth)
        assert len(result["pillars"]["gan"]) == 4
        assert len(result["pillars"]["ji"]) == 4

    @pytest.mark.parametrize("birth", BIRTHS)
    def test_no_error_in_sections(self, birth):
        result = analyze_saju(birth)
        for section in ("oheng", "shinsal"):
            data = result[section]
            if isinstance(data, dict):
                assert "error" not in data, \
                    f"{section} 에러 ({birth}): {data.get('error')}"
