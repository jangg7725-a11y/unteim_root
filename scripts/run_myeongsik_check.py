# unteim/scripts/run_myeongsik_check.py
from __future__ import annotations

from pprint import pprint

from unteim import calculate_saju

INPUT_STR = "1966-11-04 02:05"


def _pillar_text(item: dict) -> str:
    """{"gan": "...", "ji": "..."} 형태를 '갑자' 같은 문자열로 바꿔준다."""
    if not isinstance(item, dict):
        return "?"
    gan = str(item.get("gan", "") or item.get("stem", "") or "?")
    ji = str(item.get("ji", "") or item.get("branch", "") or "?")
    return f"{gan}{ji}"


def main() -> None:
    print("==== UNTEIM 명식 확인 ====")
    print(f"[입력] {INPUT_STR}")

    try:
        result = calculate_saju(INPUT_STR)
    except Exception as e:
        print(f"[오류] calculate_saju 실행 실패: {type(e).__name__}: {e}")
        return

    print("\n[전체 결과]")
    pprint(result, sort_dicts=False)

    print("\n[사주 명식]")
    labels = {
        "year": "연주",
        "month": "월주",
        "day": "일주",
        "hour": "시주",
    }

    for key in ("year", "month", "day", "hour"):
        text = _pillar_text(result.get(key, {}))
        print(f"- {labels[key]}: {text}")

    meta = result.get("meta", {})
    if isinstance(meta, dict) and meta:
        print("\n[메타 정보]")
        pprint(meta, sort_dicts=False)


if __name__ == "__main__":
    # 권장 실행:
    # python -m scripts.run_myeongsik_check
    main()
