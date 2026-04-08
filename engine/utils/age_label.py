# unteim/engine/utils/age_label.py

def age_stage_label(age: int) -> str:
    """
    나이를 받아 인생 단계 라벨을 반환
    (PDF/리포트/상담 공통 규칙)
    """
    if age < 0:
        return "출생 전"

    if age <= 7:
        return "유아기"
    elif age <= 19:
        return "청소년기"
    elif age <= 64:
        return "성인기"
    else:
        return "노년기"


def format_age_range(start_age: int, end_age: int) -> str:
    """
    PDF/문장 출력용 나이 범위 포맷
    예: 성인기(34~43세)
    """
    stage = age_stage_label(start_age)
    return f"{stage}({start_age}~{end_age}세)"
