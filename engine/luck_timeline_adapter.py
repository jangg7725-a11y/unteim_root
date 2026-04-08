# unteim/engine/luck_timeline_adapter.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal, List, Optional


LuckKind = Literal["daewoon", "sewoon", "wolwoon"]


@dataclass
class LuckSegment:
    """대운/세운/월운 공통 구간 형식"""

    kind: LuckKind           # "daewoon" | "sewoon" | "wolwoon"
    label: str               # "제4대운", "2025년", "2025-11" 등 사람이 보는 이름
    start_date: date         # 구간 시작일
    end_date: date           # 구간 종료일

    ganji: str               # 운의 간지(예: "경자", "정묘")
    oheng: str               # 운의 오행(예: "금", "목", "수" ...)

    # 아래부터는 yongshin_luck에서 채워 쓰거나, 엔진에서 미리 채워도 됨
    score: int = 0           # 용신 기준 호/주의 스코어 (-3 ~ +3 추천)
    reason: str = ""         # 왜 이런 점수가 나왔는지 메모
    tag: Optional[str] = None  # "호운", "주의", "변화", "위기" 등 라벨

# unteim/engine/luck_timeline_adapter.py (위 LuckSegment 아래에 이어서)

from datetime import datetime
from typing import List, Tuple

# ⚠️ 여기 import 부분은 오슈님 실제 엔진 이름에 맞게 고쳐줘야 함
# 예시:
# from .daewoon_engine import calculate_daewoon
# from .sewoon_engine import calculate_sewoon
# from .wolwoon_engine import calculate_wolwoon


def adapt_daewoon_to_segments(
    birth_dt: datetime,
    gender: str,
) -> List[LuckSegment]:
    """
    대운 엔진 결과를 LuckSegment 리스트로 변환.
    오슈님이 이미 가진 대운 결과 구조에 맞게 안쪽만 수정해서 쓰면 됨.
    """
    segments: List[LuckSegment] = []

    # ⚠️ 예시 코드: 실제로는 오슈님이 만든 대운 함수/결과 구조에 맞게 수정
    daewoon_list = []  # = calculate_daewoon(birth_dt, gender)

    for row in daewoon_list:
        # row 예시 가정:
        # {
        #   "index": 1,
        #   "label": "제1대운",
        #   "start_date": date(2025, 2, 4),
        #   "end_date": date(2035, 2, 3),
        #   "ganji": "경자",
        #   "oheng": "금"
        # }
        seg = LuckSegment(
            kind="daewoon",
            label=row["label"],
            start_date=row["start_date"],
            end_date=row["end_date"],
            ganji=row["ganji"],
            oheng=row["oheng"],
        )
        segments.append(seg)

    return segments


def adapt_sewoon_to_segments(
    birth_dt: datetime,
    from_year: int,
    to_year: int,
) -> List[LuckSegment]:
    """
    세운(연운) 엔진 결과를 LuckSegment 리스트로 변환.
    """
    segments: List[LuckSegment] = []

    sewoon_list = []  # = calculate_sewoon(birth_dt, from_year, to_year)

    for row in sewoon_list:
        # row 예시:
        # {
        #   "year": 2025,
        #   "ganji": "을사",
        #   "oheng": "화",
        #   "start_date": date(2025, 1, 1),
        #   "end_date": date(2025, 12, 31),
        # }
        label = f"{row['year']}년"
        seg = LuckSegment(
            kind="sewoon",
            label=label,
            start_date=row["start_date"],
            end_date=row["end_date"],
            ganji=row["ganji"],
            oheng=row["oheng"],
        )
        segments.append(seg)

    return segments


def adapt_wolwoon_to_segments(
    birth_dt: datetime,
    year: int,
) -> List[LuckSegment]:
    """
    월운 엔진 결과를 LuckSegment 리스트로 변환.
    """
    segments: List[LuckSegment] = []

    wolwoon_list = []  # = calculate_wolwoon(birth_dt, year)

    for row in wolwoon_list:
        # row 예시:
        # {
        #   "year": 2025,
        #   "month": 11,
        #   "ganji": "정해",
        #   "oheng": "수",
        #   "start_date": date(2025, 11, 1),
        #   "end_date": date(2025, 11, 30),
        # }
        label = f"{row['year']}-{row['month']:02d}"
        seg = LuckSegment(
            kind="wolwoon",
            label=label,
            start_date=row["start_date"],
            end_date=row["end_date"],
            ganji=row["ganji"],
            oheng=row["oheng"],
        )
        segments.append(seg)

    return segments
