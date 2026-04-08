# unteim/scripts/quick_check.py
from __future__ import annotations

from pprint import pprint

from unteim import calculate_saju


def main() -> None:
    print("==== UNTEIM Quick Check ====")

    birth_str = "1966-11-04 02:05"
    result = calculate_saju(birth_str)

    print(f"\n[입력] {birth_str}")
    print("\n[사주 결과 전체]")
    pprint(result, sort_dicts=False)

    print("\n[핵심 확인]")
    for key in ("year", "month", "day", "hour"):
        item = result.get(key, {})
        gan = item.get("gan", "")
        ji = item.get("ji", "")
        print(f"  - {key}: {gan}{ji}")

    meta = result.get("meta", {})
    if isinstance(meta, dict) and meta:
        print("\n[메타 정보]")
        pprint(meta, sort_dicts=False)


if __name__ == "__main__":
    # 권장 실행:
    # python -m scripts.quick_check
    main()
