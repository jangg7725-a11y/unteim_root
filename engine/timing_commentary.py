# unteim/engine/timing_commentary.py
from __future__ import annotations
from typing import List, Any


def analyze_daewoon_commentary(
    daewoon_list: List[Any],
    yongshin=None,
    oheng=None,
) -> str:
    if not daewoon_list:
        return "대운 데이터가 없어 해석을 생성할 수 없습니다."

    return (
        "대운 흐름은 인생의 큰 방향성과 환경 변화를 나타냅니다. "
        "현재 버전에서는 대운의 기둥과 시작·종료 나이를 기준으로 "
        "기초적인 흐름만 안내하며, 향후 오행·용신·격국을 반영한 "
        "정밀 해석이 추가될 예정입니다."
    )


def analyze_sewun_commentary(
    sewun_list: List[Any],
    yongshin=None,
    oheng=None,
) -> str:
    if not sewun_list:
        return "세운 데이터가 없어 해석을 생성할 수 없습니다."

    return (
        "세운은 해마다 달라지는 기운으로, 그 해의 사건·기회·주의점을 "
        "보여줍니다. 현재는 연주 기준의 기본 흐름만 제공되며, "
        "대운과의 상호작용 해석은 고도화 단계에서 추가됩니다."
    )


def analyze_wolwoon_commentary(
    wolwoon_list: List[Any],
    yongshin=None,
    oheng=None,
) -> str:
    if not wolwoon_list:
        return "월운 데이터가 없어 해석을 생성할 수 없습니다."

    return (
        "월운은 실제 체감 운세에 가장 가까운 흐름입니다. "
        "현재는 월별 기초 정보만 제공되며, 향후 일간·용신·신살을 반영한 "
        "실전형 월운 해석 문장이 추가될 예정입니다."
    )
