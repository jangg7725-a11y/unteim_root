# unteim/engine/month_stem_resolver.py
from __future__ import annotations

from typing import Dict, Optional, Union

# -----------------------------
# 기본 상수 / 매핑
# -----------------------------

# 10천간 (한자)
HEAVENLY_STEMS_HANJA = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# 12지지 한자→한글
BRANCH_HANJA_TO_KOR: Dict[str, str] = {
    "子": "자", "丑": "축", "寅": "인", "卯": "묘",
    "辰": "진", "巳": "사", "午": "오", "未": "미",
    "申": "신", "酉": "유", "戌": "술", "亥": "해",
}

# 12지지 한글→인월(寅)=1 기준 월번호
BRANCH_TO_MONTH_NO: Dict[str, int] = {
    "인": 1, "묘": 2, "진": 3, "사": 4, "오": 5, "미": 6,
    "신": 7, "유": 8, "술": 9, "해": 10, "자": 11, "축": 12,
}

# 한글 천간 → 한자 천간
GAN_KOR_TO_HANJA: Dict[str, str] = {
    "갑": "甲", "을": "乙", "병": "丙", "정": "丁", "무": "戊",
    "기": "己", "경": "庚", "신": "辛", "임": "壬", "계": "癸",
}

# 한자 천간 → 한글 천간
GAN_HANJA_TO_KOR: Dict[str, str] = {v: k for k, v in GAN_KOR_TO_HANJA.items()}

# 연간(천간) → 그룹(갑기, 을경, 병신, 정임, 무계)
# (한글/한자 둘 다 지원하도록 2세트 준비)
GAN_GROUPS_KOR: Dict[str, int] = {
    "갑": 0, "기": 0,
    "을": 1, "경": 1,
    "병": 2, "신": 2,
    "정": 3, "임": 3,
    "무": 4, "계": 4,
}
GAN_GROUPS_HANJA: Dict[str, int] = {
    "甲": 0, "己": 0,
    "乙": 1, "庚": 1,
    "丙": 2, "辛": 2,
    "丁": 3, "壬": 3,
    "戊": 4, "癸": 4,
}

# 그룹별 인월(寅월) 시작 월간(한자)
# 갑/기년: 丙寅 시작, 을/경년: 戊寅, 병/신년: 庚寅, 정/임년: 壬寅, 무/계년: 甲寅
START_STEMS_BY_GROUP = ["丙", "戊", "庚", "壬", "甲"]


# -----------------------------
# 정규화 헬퍼
# -----------------------------
def _safe_strip(v: object) -> str:
    try:
        return str(v).strip()
    except Exception:
        return ""


def _year_to_stem_hanja(year: int) -> str:
    """
    1984년 = 갑자(甲子) 기준으로 천간만 계산 (갑=0)
    """
    # (year - 1984) % 10 -> 천간 인덱스
    idx = (year - 1984) % 10
    return HEAVENLY_STEMS_HANJA[idx]


def _normalize_year_gan_to_hanja(year_gan: Union[int, str, None]) -> Optional[str]:
    """
    year_gan 입력을 한자 천간(甲..癸)로 정규화.
    허용:
      - int: 1990 같은 연도
      - str: '갑'/'甲'/'갑자'/'甲子' 등에서 첫 글자만 사용
    실패 시 None
    """
    if year_gan is None:
        return None

    # 연도(int)면 천간 계산
    if isinstance(year_gan, int):
        return _year_to_stem_hanja(year_gan)

    s = _safe_strip(year_gan)
    if not s:
        return None

    # 예: "갑자", "甲子" 같은 경우 첫 글자만 보정
    first = s[0]

    # 한자 천간이면 그대로
    if first in GAN_HANJA_TO_KOR:
        return first

    # 한글 천간이면 한자로 변환
    if first in GAN_KOR_TO_HANJA:
        return GAN_KOR_TO_HANJA[first]

    # 혹시 '甲'이 아닌데 앞뒤 공백/이상문자 섞인 케이스 방어
    # " 甲 " 같은 경우: first가 공백이 될 수 있으니 전체에서 천간 문자 탐색
    for ch in s:
        if ch in GAN_HANJA_TO_KOR:
            return ch
        if ch in GAN_KOR_TO_HANJA:
            return GAN_KOR_TO_HANJA[ch]

    return None


def _normalize_month_branch_to_kor(month_branch: Union[str, None]) -> Optional[str]:
    """
    month_branch를 한글 지지(자..해)로 정규화.
    허용:
      - '午' -> '오'
      - '오' -> '오'
      - '오월' 같은 경우 첫 글자만 처리
    실패 시 None
    """
    if month_branch is None:
        return None

    s = _safe_strip(month_branch)
    if not s:
        return None

    first = s[0]

    # 한자 지지면 한글로
    if first in BRANCH_HANJA_TO_KOR:
        return BRANCH_HANJA_TO_KOR[first]

    # 한글 지지면 그대로
    if first in BRANCH_TO_MONTH_NO:
        return first

    # 문자열 내부에 지지 문자가 섞여있는 경우 탐색
    for ch in s:
        if ch in BRANCH_HANJA_TO_KOR:
            return BRANCH_HANJA_TO_KOR[ch]
        if ch in BRANCH_TO_MONTH_NO:
            return ch

    return None


# -----------------------------
# Resolver
# -----------------------------
class MonthStemResolver:
    """
    월간(月干) 계산기

    입력:
      - year_gan: 연도(int) 또는 천간(한글/한자/간지 문자열)
      - month_branch: 지지(한글/한자/지지 문자열)

    출력:
      - 월간(한자 천간 甲..癸)
    """

    def resolve(self, year_gan: Union[int, str, None], month_branch: Union[str, None]) -> str:
        # 1) year_gan → 한자 천간
        y = _normalize_year_gan_to_hanja(year_gan)
        if not y:
            # 최종판 안정화: 인식 불가면 기본값(甲)으로 진행
            y = "甲"

        # 2) month_branch → 한글 지지
        mb_kor = _normalize_month_branch_to_kor(month_branch)
        if not mb_kor:
            raise ValueError(f"월지(지지) 인식 불가: {month_branch!r}")

        if mb_kor not in BRANCH_TO_MONTH_NO:
            raise ValueError(f"월지(지지) 없는 월지: {mb_kor!r} (원본: {month_branch!r})")

        m = BRANCH_TO_MONTH_NO[mb_kor]  # 1..12 (인월=1)

        # 3) year 천간 그룹 구하기 (한자 키로)
        g = GAN_GROUPS_HANJA.get(y)
        if g is None:
            # 혹시라도 y가 한글로 들어오는 경우 방어
            y_kor = GAN_HANJA_TO_KOR.get(y, y)
            g = GAN_GROUPS_KOR.get(y_kor)

        if g is None:
            g = 0  # fallback

        # 4) 그룹별 인월 시작 월간 → m개월 이동
        start = START_STEMS_BY_GROUP[g]  # 예: 丙
        start_idx = HEAVENLY_STEMS_HANJA.index(start)
        idx = (start_idx + (m - 1)) % 10
        return HEAVENLY_STEMS_HANJA[idx]


__all__ = ["MonthStemResolver"]
