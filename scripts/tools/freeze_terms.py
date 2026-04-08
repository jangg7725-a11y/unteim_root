# -*- coding: utf-8 -*-
"""
freeze_terms.py
1900~2100년까지의 '중기(30° 단위)' 절입 시각을 미리 계산하여 JSON 파일로 저장.
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from engine.solar_terms_compute import compute_principal_terms


def main():
    parser = argparse.ArgumentParser(description="Freeze solar terms (principal terms) to JSON.")
    parser.add_argument("--start", type=int, required=True, help="시작 연도 (예: 1900)")
    parser.add_argument("--end", type=int, required=True, help="끝 연도 (예: 2100)")
    parser.add_argument("--out", type=str, required=True, help="출력 JSON 파일 경로")
    parser.add_argument("--mode", type=str, default="compute", choices=["compute"], help="계산 모드 (고정=없음, 항상 compute)")
    args = parser.parse_args()

    data = {}
    for year in range(args.start, args.end + 1):
        terms = compute_principal_terms(year)  # ← 항상 계산기로 호출
        clean = [
            {"degree": int(t["degree"]), "time_utc": str(t["time_utc"])}
            for t in terms
            if int(t["degree"]) % 30 == 0
        ]
        data[str(year)] = clean

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[✅] principal_terms.json 저장 완료: {args.out}")


if __name__ == "__main__":
    main()
