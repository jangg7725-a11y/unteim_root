# -*- coding: utf-8 -*-
"""
lunar_bazi_preview.py
음력 입력 → 양력 변환 → 사주명식(년/월/일/시) 프리뷰

사용 예)
  python -m engine.lunar_bazi_preview ^
    --lunar 1966-11-04 --time 02:05 --gender 여 --yinyang 양 --sewun ipchun
  # 윤달이면 --leap 추가
"""

from __future__ import annotations

import argparse
from typing import Any, Dict, Tuple, Optional, cast

# 프로젝트 내부 의존
from .daewoonCalculator import Gender, YinYang
from .luckTimeline import build_daewoon_sewun_timeline, SewunBoundary


# -------------------------------
# 1) kasi_client의 음→양 변환을 동적으로 해석
# -------------------------------
def _resolve_lunar_to_solar():
    """
    kasi_client에 정의된 lunar_to_solar (또는 convert_lunar_to_solar) 함수를 찾아 반환
    """
    import importlib
    kc = importlib.import_module("engine.kasi_client")
    if hasattr(kc, "lunar_to_solar"):
        return getattr(kc, "lunar_to_solar")
    if hasattr(kc, "convert_lunar_to_solar"):
        return getattr(kc, "convert_lunar_to_solar")
    raise RuntimeError("kasi_client에 lunar_to_solar/convert_lunar_to_solar 함수가 없습니다.")


def _convert_lunar_to_solar(lunar_ymd: str, is_leap: bool) -> Tuple[int, int, int]:
    fn = _resolve_lunar_to_solar()
    y, m, d = map(int, lunar_ymd.split("-"))
    try:
        # (y, m, d, is_leap) 시그니처 우선 시도
        res = fn(y, m, d, is_leap)
    except TypeError:
        # dict 인자 시그니처 대응
        res = fn({"year": y, "month": m, "day": d, "is_leap": is_leap})

    if isinstance(res, (list, tuple)) and len(res) >= 3:
        return int(res[0]), int(res[1]), int(res[2])
    if isinstance(res, dict):
        return int(res["year"]), int(res["month"]), int(res["day"])
    raise RuntimeError("음→양 변환 결과 형식을 인식할 수 없습니다.")


# -------------------------------
# 2) 출력 유틸
# -------------------------------
def _pair_to_str(v: Any) -> str:
    """('간','지') 또는 ['간','지'] → '간지'로 포매팅"""
    if isinstance(v, (list, tuple)) and len(v) >= 2:
        return f"{v[0]}{v[1]}"
    return "?"


def _print_title():
    print("=== 음력 입력 → 사주명식 프리뷰 ===")


def _print_input_and_conv(lunar: str, leap: bool, time_str: str, sy: int, sm: int, sd: int, hh: int, mm: int, sewun: str):
    print(f"- 입력(음력):   {lunar} {'(윤달)' if leap else ''} {time_str} KST")
    print(f"- 변환(양력):   {sy:04d}-{sm:02d}-{sd:02d} {hh:02d}:{mm:02d} KST")
    print(f"- 기준(월/연):  절기기준={sewun}  (ipchun 권장)")
    print("")


def _print_pillars(base_pillars: Dict[str, Any], meta: Dict[str, Any]) -> None:
    print("사주명식(간지 네 기둥)")
    print(f"  년주: {_pair_to_str(base_pillars.get('year'))}")
    print(f"  월주: {_pair_to_str(base_pillars.get('month'))}")
    print(f"  일주: {_pair_to_str(base_pillars.get('day'))}")
    print(f"  시주: {_pair_to_str(base_pillars.get('hour'))}")

    # 보조 정보가 있으면 같이
    mb = meta.get("month_branch_actual")
    if mb:
        print(f"\n(참고) 절입 보정된 실제 월지: {mb}")
    ts = meta.get("twelve_stage")
    if ts:
        print(f"(참고) 월지 기준 12운성: {ts}")


def _print_debug_meta(meta: Dict[str, Any]) -> None:
    """base_pillars가 없을 때, 디버그용으로 메타 키를 보여준다."""
    print("\n[참고] base_pillars가 비어있습니다. 메타 키를 출력합니다.")
    keys = sorted(list(meta.keys()))
    print("  __meta__ keys:", ", ".join(keys) if keys else "(없음)")
    # 혹시 다른 이름으로 존재하는지 대략 스캔
    for k in keys:
        if "pillar" in k or "ganji" in k or "base" in k:
            print(f"  - {k} = {meta.get(k)}")


# -------------------------------
# 3) 메인
# -------------------------------
def main():
    ap = argparse.ArgumentParser(description="음력 입력 → 양력 변환 → 사주명식 프리뷰")
    ap.add_argument("--lunar", required=True, help="음력 생일 YYYY-MM-DD")
    ap.add_argument("--leap", action="store_true", help="윤달이면 지정")
    ap.add_argument("--time", default="00:00", help="출생 시각 HH:MM (KST)")
    ap.add_argument("--gender", choices=["남","여"], required=True)
    ap.add_argument("--yinyang", choices=["양","음"], required=True)
    ap.add_argument("--sewun", choices=["ipchun","jan1"], default="ipchun", help="세운/연월 경계: ipchun 권장")
    args = ap.parse_args()

    # 1) 음력 → 양력 변환
    sy, sm, sd = _convert_lunar_to_solar(args.lunar, args.leap)
    hh, mm = map(int, args.time.split(":"))

    # 2) 프로젝트 정식 로직으로 메타 생성 (여기에 base_pillars가 포함되도록 구성됨)
    data: Dict[str, Any] = build_daewoon_sewun_timeline(
        birth_year=sy,
        gender=cast(Gender, args.gender),
        yin_yang=cast(YinYang, args.yinyang),
        birth_month=sm,
        birth_day=sd,
        birth_hour=hh,
        birth_minute=mm,
        num_cycles=1,                 # 프리뷰라 1사이클만
        use_month_pillar=True,        # 월주는 절기 기준
        sewun_boundary=cast(SewunBoundary, args.sewun),
        include_months=False,
        include_days=False,
    )

    meta = cast(Dict[str, Any], data.get("__meta__", {}))
    base_pillars = cast(Dict[str, Any], meta.get("base_pillars", {}))

    # 3) 출력
    _print_title()
    _print_input_and_conv(
        args.lunar, args.leap, args.time,
        sy, sm, sd, hh, mm,
        cast(str, args.sewun),
    )

    if base_pillars and all(k in base_pillars for k in ("year","month","day","hour")):
        _print_pillars(base_pillars, meta)
    else:
        # 안전망: 메타가 없다면 디버그 정보 제공
        print("사주명식(간지 네 기둥)")
        print("  년주: ?")
        print("  월주: ?")
        print("  일주: ?")
        print("  시주: ?")
        _print_debug_meta(meta)
        print("\n[안내] base_pillars가 비어 있으면 다음을 확인하세요:")
        print("  - luckTimeline.build_daewoon_sewun_timeline 내에서 '__meta__['base_pillars']' 주입 로직이 있는지")
        print("  - sewun 경계가 ipchun인지 (연/월주가 절입 기준으로 계산되도록 권장)")
        print("  - 출생 시각이 KST(UTC+9) 기준으로 전달되는지")


if __name__ == "__main__":
    main()
