from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from engine.sajuCalculator import analyze_saju, calculate_saju


ROOT = Path(__file__).resolve().parents[1]
SAMPLES_PATH = ROOT / "data" / "verification" / "saju_accuracy_samples_v1.json"


def _load_samples() -> List[Dict[str, Any]]:
    raw = json.loads(SAMPLES_PATH.read_text(encoding="utf-8"))
    return raw.get("samples", [])


SAMPLES = _load_samples()


def _pillar_obj_to_dict(pillars_obj: Any) -> Dict[str, str]:
    if hasattr(pillars_obj, "as_dict"):
        d = pillars_obj.as_dict()
    else:
        d = pillars_obj
    if not isinstance(d, dict):
        return {"year": "", "month": "", "day": "", "hour": ""}
    out: Dict[str, str] = {}
    for k in ("year", "month", "day", "hour"):
        blk = d.get(k)
        if isinstance(blk, dict):
            out[k] = f"{blk.get('gan', '')}{blk.get('ji', '')}"
        else:
            out[k] = ""
    return out


def _assert_optional_pillar_expectation(expected_val: Any, actual_val: str, label: str) -> None:
    # None: 검증 생략
    if expected_val is None:
        return
    exp = str(expected_val)
    # '?子' 형태: 지지(2번째 문자)만 고정
    if exp.startswith("?") and len(exp) >= 2:
        assert actual_val.endswith(exp[1:]), f"{label} 기대 지지={exp[1:]}, 실제={actual_val}"
        return
    assert actual_val == exp, f"{label} 기대={exp}, 실제={actual_val}"


def test_sample_file_schema_minimum() -> None:
    assert SAMPLES_PATH.is_file(), f"샘플 파일 없음: {SAMPLES_PATH}"
    assert isinstance(SAMPLES, list)
    assert len(SAMPLES) >= 10, f"샘플 수 부족: {len(SAMPLES)}"
    for s in SAMPLES:
        assert "id" in s
        assert "input" in s and isinstance(s["input"], dict)
        assert "expected" in s and isinstance(s["expected"], dict)
        p = s["expected"].get("pillars")
        assert isinstance(p, dict)
        for k in ("year", "month", "day", "hour"):
            assert k in p
        # 요구사항: 각 샘플에 기대 오행/십신/12운성/공망 키 구조 포함
        for k in ("oheng_counts", "shinsal_contains", "twelve_fortunes_contains", "kongmang", "yongshin"):
            assert k in s["expected"], f"expected.{k} 누락: {s['id']}"


@pytest.mark.parametrize("sample", SAMPLES, ids=[s["id"] for s in SAMPLES])
def test_core_pillar_and_engine_regression(sample: Dict[str, Any]) -> None:
    birth = sample["input"]["birth_str"]
    calendar = sample["input"].get("calendar", "solar")
    sex = sample["input"].get("sex", "F")
    expected = sample["expected"]
    exp_p = expected["pillars"]

    pillars = calculate_saju(birth, gender=sex, calendar=calendar)
    actual_p = _pillar_obj_to_dict(pillars)

    _assert_optional_pillar_expectation(exp_p.get("year"), actual_p["year"], f"{sample['id']} year")
    _assert_optional_pillar_expectation(exp_p.get("month"), actual_p["month"], f"{sample['id']} month")
    _assert_optional_pillar_expectation(exp_p.get("day"), actual_p["day"], f"{sample['id']} day")
    _assert_optional_pillar_expectation(exp_p.get("hour"), actual_p["hour"], f"{sample['id']} hour")

    # ---- analyze_saju 단에서 오행/신살/운 흐름 회귀 ----
    result = analyze_saju(birth, gender=sex, calendar=calendar)
    assert isinstance(result, dict)

    # 오행 불변식(전 샘플 공통): 5원소 키 존재
    oh = result.get("oheng", {})
    assert isinstance(oh, dict), f"{sample['id']} oheng 타입 오류"
    counts = oh.get("counts", {})
    assert isinstance(counts, dict), f"{sample['id']} oheng.counts 타입 오류"
    for elem in ("木", "火", "土", "金", "水"):
        assert elem in counts, f"{sample['id']} 오행 키 누락: {elem}"

    # known-value(있을 때만 exact)
    expected_counts = expected.get("oheng_counts")
    if isinstance(expected_counts, dict):
        for k, v in expected_counts.items():
            assert counts.get(k) == v, f"{sample['id']} oheng {k} 기대={v}, 실제={counts.get(k)}"

    # 신살 포함 문자열(있을 때만)
    shinsal_contains = expected.get("shinsal_contains") or []
    if shinsal_contains:
        sh = result.get("shinsal", {})
        assert isinstance(sh, dict)
        sh_text = json.dumps(sh, ensure_ascii=False)
        for token in shinsal_contains:
            assert token in sh_text, f"{sample['id']} 신살 토큰 누락: {token}"

    # 12운성 포함 문자열(있을 때만)
    tf_contains = expected.get("twelve_fortunes_contains") or []
    if tf_contains:
        tf_text = json.dumps(result.get("twelve_fortunes"), ensure_ascii=False)
        for token in tf_contains:
            assert token in tf_text, f"{sample['id']} 12운성 토큰 누락: {token}"

    # 우선순위 10: 대운/sewun/월운 최소 구조 검증
    for lk in ("daewoon", "sewun", "wolwoon"):
        assert lk in result, f"{sample['id']} {lk} 누락"
        assert isinstance(result[lk], list), f"{sample['id']} {lk} 타입 오류"
