from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COVERAGE_PATH = ROOT / "data" / "verification" / "engine_validation_coverage_v1.json"


def test_coverage_file_exists_and_has_priorities() -> None:
    assert COVERAGE_PATH.is_file(), f"coverage file missing: {COVERAGE_PATH}"
    raw = json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))
    rows = raw.get("coverage", [])
    assert isinstance(rows, list)
    assert len(rows) == 10, f"우선순위 10개여야 함. 현재={len(rows)}"

    priorities = sorted(int(r.get("priority")) for r in rows)
    assert priorities == list(range(1, 11))


def test_insufficient_baseline_is_explicitly_marked() -> None:
    raw = json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))
    rows = raw.get("coverage", [])
    marked = [r for r in rows if r.get("status") == "insufficient_baseline"]
    names = {str(r.get("name")) for r in marked}
    # 현재 기준 데이터가 부족한 엔진은 명시적으로 관리
    assert any("공망" in n for n in names)
    assert any("용신" in n for n in names)
