# tests/test_samjae_engine_v1.py
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.samjae_engine_v1 import (
    build_samjae_result,
    build_samjae_bundle_v2,
    _prev_next_branches,
    SAMJAE_START,
)


def _packed(year_ji: str, sewun_year: int, sewun_branch: str) -> dict:
    """세운 연지는 2글자 간지에서 두 번째 글자로 추출된다."""
    return {
        "meta": {"year": sewun_year},
        "pillars": {"year": {"ji": year_ji}},
        "sewun": [{"year": sewun_year, "year_pillar": f"X{sewun_branch}"}],
    }


def test_prev_next_branches_yin_pivot():
    d, n = _prev_next_branches("寅")
    assert d == "丑"
    assert n == "卯"


def test_samjae_sin_ja_jin_year_deul_nul_nal():
    # 신자진 그룹 → 눌(본삼재) 지지 = 寅
    assert SAMJAE_START["신자진"] == "寅"
    y = 2026
    # 들=丑 눌=寅 날=卯
    r_deul = build_samjae_result(_packed("申", y, "丑"))
    assert r_deul["is_samjae"] and r_deul["stage"] == "들삼재" and r_deul["stage_code"] == "deul"

    r_nul = build_samjae_result(_packed("申", y, "寅"))
    assert r_nul["is_samjae"] and r_nul["stage"] == "눌삼재" and r_nul["stage_code"] == "nul"

    r_nal = build_samjae_result(_packed("申", y, "卯"))
    assert r_nal["is_samjae"] and r_nal["stage"] == "날삼재" and r_nal["stage_code"] == "nal"


def test_samjae_not_in_window():
    y = 2026
    r = build_samjae_result(_packed("申", y, "辰"))  # 삼재 삼 지지 밖 (눌 직후 다음 …)
    assert not r["is_samjae"]
    assert r["stage"] is None


def test_bundle_v2_phase_weight_mapping():
    y = 2026
    b = build_samjae_bundle_v2(_packed("申", y, "丑"))
    assert b.get("is_samjae")
    # 들삼재 → 입력 가중치 3
    assert b.get("risk_level") in (2, 3, 4)  # 조정 전 기대: 기본 3 ± 플래그


def test_bundle_v2_nal_lower_base_risk():
    y = 2026
    b_nal = build_samjae_bundle_v2(_packed("申", y, "卯"))
    b_deul = build_samjae_bundle_v2(_packed("申", y, "丑"))
    assert b_nal.get("risk_level") is not None and b_deul.get("risk_level") is not None
    # 동일 플래그(없음)일 때 날삼재 기본값이 들삼재보다 낮다
    assert b_nal["risk_level"] < b_deul["risk_level"]
