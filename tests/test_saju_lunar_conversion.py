from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

import pytest

from engine.timing_engine import _try_solar_to_lunar


ROOT = Path(__file__).resolve().parents[1]
LUNAR_SAMPLES_PATH = ROOT / "data" / "verification" / "lunar_conversion_samples_v1.json"


def _load_samples() -> List[Dict[str, Any]]:
    raw = json.loads(LUNAR_SAMPLES_PATH.read_text(encoding="utf-8"))
    return raw.get("samples", [])


SAMPLES = _load_samples()


def test_lunar_sample_file_schema() -> None:
    assert LUNAR_SAMPLES_PATH.is_file()
    assert len(SAMPLES) >= 3
    for s in SAMPLES:
        assert "id" in s
        assert "solar_date" in s
        assert "expected_lunar" in s
        exp = s["expected_lunar"]
        for k in ("year", "month", "day", "is_leap"):
            assert k in exp


@pytest.mark.parametrize("sample", SAMPLES, ids=[s["id"] for s in SAMPLES])
def test_solar_to_lunar_known_dates(sample: Dict[str, Any]) -> None:
    y, m, d = [int(x) for x in sample["solar_date"].split("-")]
    got = _try_solar_to_lunar(date(y, m, d))

    # KASI 연결 실패 환경(오프라인/차단)에서는 스킵
    if got is None:
        pytest.skip("KASI solar->lunar unavailable in this environment")

    ey = int(sample["expected_lunar"]["year"])
    em = int(sample["expected_lunar"]["month"])
    ed = int(sample["expected_lunar"]["day"])
    el = bool(sample["expected_lunar"]["is_leap"])

    gy, gm, gd, gl = got
    assert (gy, gm, gd) == (ey, em, ed), f"{sample['id']} 기대={(ey, em, ed)}, 실제={(gy, gm, gd)}"

    # medium confidence 샘플은 윤달 bool만 체크 강도 완화 가능
    conf = str(sample.get("confidence") or "high")
    if conf == "high":
        assert gl == el, f"{sample['id']} 윤달 기대={el}, 실제={gl}"
    else:
        # 중간 신뢰 샘플은 윤달 처리 파이프라인이 bool을 반환하는지 우선 고정
        assert isinstance(gl, bool)
