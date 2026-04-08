# -*- coding: utf-8 -*-
"""
seed_year_terms.py
- 지정 연도의 24절기를 KASI API를 '분산 탐색'으로 확보하여
  SQLite에 저장합니다. (레이트리밋 회피용으로 여유 있게 호출)
- 이미 저장된 항목은 upsert로 갱신/유지합니다.
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Set

from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_ROOT / ".env")

from engine.kasi_client import fetch_solarterm
from engine.calendar_store import init_schema, upsert_solar_term, get_solar_terms

# 월별로 1/8/15/22일만 콕콕 찍어도 대부분 절기를 커버합니다.
# (KASI가 '그 날짜에 인접한 절입' 정보를 반환하는 형태이므로.)
PROBE_DAYS = (1, 8, 15, 22)

def _parse_iso_year(iso: str) -> int:
    # "YYYY-MM-DDTHH:MM:SS+09:00" → YYYY
    return int(iso[0:4])

def seed_year(year: int, sleep_sec: float = 1.2) -> Dict[str, str]:
    """
    지정 연도(year)의 절기(이름→시각KST)를 DB에 저장하고,
    최종적으로 수집된 {term_name: iso_kst} dict를 반환합니다.
    """
    init_schema()

    found: Dict[str, str] = {}
    seen_names: Set[str] = set()

    for m in range(1, 13):
        for d in PROBE_DAYS:
            try:
                dt = datetime(year, m, d)
            except ValueError:
                continue  # (예: 2/30 같은 날짜 회피)
            date_str = dt.strftime("%Y-%m-%d")
            info = fetch_solarterm(date_str)  # 네트워크 또는 캐시
            term = getattr(info, "term_name", "") or ""
            iso  = getattr(info, "term_datetime", "") or ""

            if not term or not iso:
                # 간혹 빈 값이 올 수 있으므로 skip
                time.sleep(sleep_sec)
                continue

            # 절기 시각의 '실제 연도' 기준으로 저장 (12/31 ~ 1/1 경계 안전)
            iso_year = _parse_iso_year(iso)
            upsert_solar_term(iso_year, term, iso)

            # 요청한 타겟연도와 같으면 found에 표시
            if iso_year == year:
                found[term] = iso
                seen_names.add(term)

            print(f"[{date_str}] -> {term} @ {iso} (iso_year={iso_year})")

            # 24개 다 모였으면 빠져나옴
            if len(seen_names) >= 24:
                break
            time.sleep(sleep_sec)
        if len(seen_names) >= 24:
            break

    # 결과 요약
    print(f"[done] year={year}, collected={len(seen_names)} terms")
    # 현재 DB에 들어있는 목록을 보여줌
    rows = get_solar_terms(year)
    for name, iso in rows:
        print(f" - {name}: {iso}")

    return found

if __name__ == "__main__":
    y = datetime.now().year
    seed_year(y)          # 올해
    seed_year(y + 1)      # 내년
    print("[ok] seeded current & next year")
