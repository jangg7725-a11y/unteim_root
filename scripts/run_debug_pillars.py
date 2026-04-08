# unteim/scripts/run_debug_pillars.py
from __future__ import annotations

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from pprint import pprint

from engine.sajuCalculator import calculate_saju


INPUT_STR = "1966-11-04 02:05"


def _safe_call_method(obj, method_name: str):
    if not hasattr(obj, method_name):
        return None, f"{method_name} 없음"
    try:
        value = getattr(obj, method_name)()
        return value, None
    except Exception as e:
        return None, f"{method_name} 실행 실패: {type(e).__name__}: {e}"


def _print_basic_info(res) -> None:
    print("==== Debug Pillars ====")
    print(f"[입력] {INPUT_STR}")
    print(f"[결과 타입] {type(res)}")

    attrs = [a for a in dir(res) if not a.startswith("_")]
    print("\n[공개 속성 목록]")
    pprint(attrs, sort_dicts=False)


def _print_raw_object(res) -> None:
    print("\n[원시 객체 __dict__]")
    try:
        pprint(vars(res), sort_dicts=False)
    except Exception as e:
        print(f"vars(res) 확인 실패: {type(e).__name__}: {e}")


def _print_methods_if_any(res) -> None:
    print("\n[가능한 변환 메서드 확인]")
    for method_name in ("as_dict", "to_dict", "to_json", "dict", "model_dump"):
        value, error = _safe_call_method(res, method_name)
        if error:
            print(f"- {error}")
        else:
            print(f"- {method_name}() 결과:")
            pprint(value, sort_dicts=False)


def _print_pillars(res) -> None:
    gan = getattr(res, "gan", None)
    ji = getattr(res, "ji", None)

    print("\n[gan / ji 배열 확인]")
    print("gan =", gan)
    print("ji  =", ji)

    if isinstance(gan, (list, tuple)) and isinstance(ji, (list, tuple)) and len(gan) == 4 and len(ji) == 4:
        labels = ("year", "month", "day", "hour")
        print("\n[기둥별 간지]")
        for i, label in enumerate(labels):
            print(f"  - {label}: {gan[i]}{ji[i]}")
    else:
        print("gan/ji 구조가 예상과 다릅니다. (길이 4의 list/tuple 아님)")


def _print_meta(res) -> None:
    meta = getattr(res, "meta", None)
    print("\n[meta 확인]")
    if isinstance(meta, dict) and meta:
        pprint(meta, sort_dicts=False)
    else:
        print(meta)


def main() -> None:
    res = calculate_saju(INPUT_STR)

    _print_basic_info(res)
    _print_raw_object(res)
    _print_methods_if_any(res)
    _print_pillars(res)
    _print_meta(res)


if __name__ == "__main__":
    # 권장 실행:
    # python -m scripts.run_debug_pillars
    main()
