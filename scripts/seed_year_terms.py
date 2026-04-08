# unteim/scripts/seed_year_terms.py
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import argparse
import json
from pathlib import Path
from typing import Any, Dict
from dataclasses import asdict, is_dataclass

# ✅ 절기 데이터 공급자 (kasi_client 합격본)
from engine.kasi_client import fetch_kasi_data




def _to_dict(obj: Any) -> Any:
    """
    JSON 저장 가능 형태로 변환
    - list/tuple 은 먼저 처리 (가장 중요)
    - dataclass 는 asdict 사용
    - dict 는 재귀 처리
    - 그 외는 그대로
    """
    if obj is None:
        return None

    # ✅ 1) 리스트/튜플 우선 처리 (이게 핵심)
    if isinstance(obj, (list, tuple)):
        return [_to_dict(x) for x in obj]

    # ✅ 2) dict 처리
    if isinstance(obj, dict):
        return {k: _to_dict(v) for k, v in obj.items()}

    # ✅ 3) dataclass 처리
    if is_dataclass(obj):
        try:
            return asdict(obj)  # type: ignore[arg-type]

        except Exception:
            return obj.__dict__

    return obj





def seed_year(year: int, out_path: Path) -> None:
    print(f"[INFO] seeding solar terms: year={year}")

    data = fetch_kasi_data(year)  # 기대: Dict[str, SolarTerm] 또는 유사 구조
    payload: Dict[str, Any] = {
       "year": year,
       "solar_terms": _to_dict(data),
    }



    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] wrote: {out_path}")


def main() -> None:
    p = argparse.ArgumentParser(description="Seed KASI solar terms into JSON")
    p.add_argument("--year", type=int, required=True, help="year, e.g. 2026")
    p.add_argument("--out", type=str, default="", help="output json path (optional)")
    args = p.parse_args()

    out = Path(args.out) if args.out else Path(f"terms_{args.year}.json")
    seed_year(args.year, out)


if __name__ == "__main__":
    main()
