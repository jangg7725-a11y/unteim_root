# unteim/engine/check_full_analyzer.py
from __future__ import annotations

from pprint import pprint
from datetime import datetime

def _safe_import():
    from engine.full_analyzer import analyze_full
    return analyze_full

def _make_minimal_pillars():
    """
    ⚠️ 이 pilllars 구조는 '최소 실행' 테스트용입니다.
    오슈님 프로젝트의 pillars 타입(GanJi 등)에 맞게 이미 있는 생성 함수를 쓰는 게 최선이지만,
    지금은 full_analyzer가 '어디서 깨지는지' 확인이 목적이라 최소 dict로 만듭니다.
    """
    class _P:
        def __init__(self, branch: str):
            self.branch = branch

    # year/month/day/hour는 현재 코드 흐름에서 다양한 모듈이 접근할 수 있으니 최소 형태만 제공
    return {
        "year": _P("자"),
        "month": _P("축"),
        "day": _P("인"),
        "hour": _P("묘"),
    }

def main():
    analyze_full = _safe_import()
    pillars = _make_minimal_pillars()

    # birth_str 형식은 full_analyzer에서 "%Y-%m-%d %H:%M" 로 파싱
    birth_str = "1990-01-01 09:30"

    print("\n=== 1) analyze_full 호출 시작 ===")
    result = analyze_full(pillars=pillars, birth_str=birth_str)

    print("\n=== 2) 결과 키 확인 ===")
    print("keys:", list(result.keys()))

    print("\n=== 3) when(시기) 확인 ===")
    pprint(result.get("when"))

    print("\n=== 4) luck_flow 구조 확인 ===")
    lf = result.get("luck_flow", {})
    print("luck_flow keys:", list(lf.keys()) if isinstance(lf, dict) else type(lf))

    print("\n=== 5) 전체 결과 일부 출력 ===")
    pprint({k: result[k] for k in ["oheng", "sipsin", "geukguk", "yongshin"] if k in result})

if __name__ == "__main__":
    main()
