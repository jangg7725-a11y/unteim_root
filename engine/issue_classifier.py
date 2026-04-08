# -*- coding: utf-8 -*-
"""
issue_classifier.py
월별/일별 사주 데이터를 바탕으로 건강·연애·재물·사기·관재 등
주요 이슈 태그를 분류하는 모듈
"""

from typing import List, Dict


def classify_issues(oheng_balance: Dict[str, int],
                    shinsal: List[str],
                    sipshin: List[str],
                    month_ganji: str) -> List[str]:
    """
    주어진 사주 요소를 바탕으로 주요 이슈 태그를 반환
    :param oheng_balance: {'목': +2, '화': -1, ...}
    :param shinsal: ['역마', '도화', '겁재', ...]
    :param sipshin: ['정재', '편재', '정관', '비견', ...]
    :param month_ganji: 현재 월지(간지)
    :return: ['health', 'love', 'money', ...]
    """

    tags = []

    # 🩺 건강 이슈 (수/목 약하거나 충·형 많을 때)
    if oheng_balance.get("수", 0) < -1 or "역마" in shinsal:
        tags.append("health")

    # 💕 연애/관계 (도화살, 홍염살, 배우자궁 충)
    if "도화" in shinsal or "홍염" in shinsal:
        tags.append("love")

    # 💰 재물 (재성 과다·겁재, 편재 강세)
    if "편재" in sipshin or "겁재" in sipshin:
        tags.append("money")

    # 🛑 사기/손재 (겁재 + 충, 또는 망신살 포함)
    if "겁재" in sipshin and ("충" in month_ganji or "망신" in shinsal):
        tags.append("fraud")

    # ⚖️ 관재/법적 (관성 충·형, 관살 혼잡)
    if "정관" in sipshin or "편관" in sipshin:
        if "충" in month_ganji or "괴강" in shinsal:
            tags.append("lawsuit")

    return tags


if __name__ == "__main__":
    # ✅ 테스트 샘플
    oheng = {"목": -2, "화": 1, "토": 0, "금": 2, "수": -1}
    shinsal = ["역마", "망신"]
    sipshin = ["편재", "겁재"]
    month = "갑자(충)"

    print("이슈 태그:", classify_issues(oheng, shinsal, sipshin, month))
    # 출력 예: ['health', 'money', 'fraud']
