# test_sentence_structure.py

# ==========================================
# 🔥 운트임 문장 역할 분리 테스트 코드
# ==========================================

import json
import os

# ------------------------------------------
# 1. 파일 경로 설정
# ------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# 👉 JSON 파일 위치 (수정 필요하면 여기만 변경)
JSON_PATH = os.path.join(BASE_DIR, "data", "sentence_db.json")


# ------------------------------------------
# 2. JSON 로드
# ------------------------------------------
def load_sentences():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


# ------------------------------------------
# 3. 역할 분리 함수 (핵심)
# ------------------------------------------
def classify_sentence(text):
    """
    문장을 역할별로 분류
    """

    # WHY (이유 설명)
    if any(k in text for k in ["이유", "때문", "패턴", "반복"]):
        return "WHY"

    # ACTION (행동)
    if any(k in text for k in ["해보세요", "하세요", "추천", "실천"]):
        return "ACTION"

    # 기본은 패턴 (자기이해)
    return "PATTERN"


# ------------------------------------------
# 4. 전체 분류 실행
# ------------------------------------------
def run_test():
    data = load_sentences()

    results = {
        "WHY": [],
        "ACTION": [],
        "PATTERN": []
    }

    # 🔥 핵심: A파트 기준 테스트
    for section_key, section in data["parts"]["A"]["sections"].items():
        for item in section["sentences"]:
            text = item["text"]

            role = classify_sentence(text)
            results[role].append(text)

    return results


# ------------------------------------------
# 5. 출력
# ------------------------------------------
def print_results(results):
    print("\n==============================")
    print("🔥 문장 역할 분리 테스트 결과")
    print("==============================\n")

    for key, sentences in results.items():
        print(f"\n▶ {key} ({len(sentences)}개)")
        print("-" * 40)

        # 앞 5개만 출력
        for s in sentences[:5]:
            print(f"- {s}")

    print("\n==============================")
    print("✅ 테스트 완료")
    print("==============================\n")


# ------------------------------------------
# 6. 실행
# ------------------------------------------
if __name__ == "__main__":
    results = run_test()
    print_results(results)