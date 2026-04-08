# unteim/scripts/run_dump_engine.py
from __future__ import annotations

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import json
from datetime import date, datetime
from pathlib import Path
from pprint import pprint

from engine.sajuCalculator import analyze_saju

INPUT_STR = "1966-11-04 02:05"
JSON_OUT = Path("out/engine_dump.json")


def _to_plain(value):
    """dict/list/datetime/dataclass-like 객체를 JSON 저장 가능한 형태로 변환"""
    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, dict):
        return {str(k): _to_plain(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [_to_plain(v) for v in value]

    if hasattr(value, "__dict__"):
        data = {}
        for k, v in vars(value).items():
            if not str(k).startswith("_"):
                data[str(k)] = _to_plain(v)
        return data

    return str(value)


def walk(name, value, indent=0):
    """결과 구조를 트리처럼 출력"""
    pad = "  " * indent

    if isinstance(value, dict):
        print(f"{pad}- {name}: dict({len(value)})")
        for k, v in value.items():
            walk(str(k), v, indent + 1)
        return

    if isinstance(value, list):
        print(f"{pad}- {name}: list({len(value)})")
        preview_count = 5
        for i, item in enumerate(value[:preview_count]):
            walk(f"[{i}]", item, indent + 1)
        if len(value) > preview_count:
            print(f"{pad}  ... ({len(value) - preview_count}개 항목 더 있음)")
        return

    print(f"{pad}- {name}: {type(value).__name__} = {value}")


def main() -> None:
    print("==== UNTEIM Engine Dump ====")
    print(f"[입력] {INPUT_STR}")

    result = analyze_saju(INPUT_STR)
    plain = _to_plain(result)

    print("\n[상위 키]")
    if isinstance(plain, dict):
        print(list(plain.keys()))
    else:
        print(type(plain).__name__)

    print("\n[전체 결과 pprint]")
    pprint(plain, sort_dicts=False)

    print("\n[구조 트리]")
    walk("result", plain)

    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(
        json.dumps(plain, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\n[저장 완료] {JSON_OUT}")
    print("\n권장 실행 명령:")
    print("python -m scripts.run_dump_engine")


if __name__ == "__main__":
    main()
