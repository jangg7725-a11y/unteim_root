# unteim/engine/output_schema.py
"""
UNTEIM analyze_saju() 결과 JSON 스키마 정의서

이 파일은 analyze_saju()가 반환하는 dict의
키 이름, 타입, 기본값을 공식적으로 정의합니다.

버전: 1.0
"""
from __future__ import annotations

# ============================================================
# 스키마 버전
# ============================================================
SCHEMA_VERSION = "1.0"

# ============================================================
# 최상위 키 목록 (반드시 존재해야 하는 키)
# ============================================================
REQUIRED_TOP_KEYS = [
    "birth_str",   # str: 입력 생년월일 문자열
    "pillars",     # dict: 사주 기둥 정보
    "oheng",       # dict: 오행 분석 결과
    "shinsal",     # dict: 신살 분석 결과
    "wolwoon",     # list: 월운 정보
    "sewun",       # list: 세운 정보
    "daewoon",     # list: 대운 정보
]

# ============================================================
# pillars 내부 구조
# ============================================================
# pillars = {
#     "gan": [str, str, str, str],  # 천간 4개 (연/월/일/시)
#     "ji":  [str, str, str, str],  # 지지 4개 (연/월/일/시)
#     "meta": {
#         "month_term": str | None,         # 월절기 이름
#         "month_term_time_kst": str | None, # 월절기 시간 (ISO)
#     }
# }
PILLARS_REQUIRED_KEYS = ["gan", "ji", "meta"]

# ============================================================
# oheng 내부 구조
# ============================================================
# oheng = {
#     "counts": {"木": int, "火": int, "土": int, "金": int, "水": int},
#     "tips": [str, ...],
#     "summary": str,
# }
OHENG_REQUIRED_KEYS = ["counts", "summary"]
OHENG_ELEMENT_NAMES = ["木", "火", "土", "金", "水"]

# ============================================================
# shinsal 내부 구조
# ============================================================
# shinsal = {
#     "items": [
#         {"name": str, "where": str, "branch": str, "detail": str, "weight": int},
#         ...
#     ],
#     "summary": {
#         "good_total": int,
#         "bad_total": int,
#         "total": int,
#         "verdict": str,
#         "by_where": dict,
#     }
# }
SHINSAL_ITEM_KEYS = ["name", "where", "branch", "detail", "weight"]
SHINSAL_SUMMARY_KEYS = ["good_total", "bad_total", "total", "verdict"]

# ============================================================
# wolwoon 항목 구조
# ============================================================
# wolwoon[i] = {
#     "start": str,          # ISO datetime
#     "end": str,            # ISO datetime
#     "term": str,           # 절기 이름
#     "month_branch": str,   # 월지
#     "month_stem": str,     # 월간
#     "month_pillar": str,   # 월주 간지
# }
WOLWOON_ITEM_KEYS = ["start", "end", "term", "month_branch", "month_stem", "month_pillar"]

# ============================================================
# sewun 항목 구조
# ============================================================
# sewun[i] = {
#     "year": int,
#     "year_pillar": str,
# }
SEWUN_ITEM_KEYS = ["year", "year_pillar"]

# ============================================================
# daewoon 항목 구조
# ============================================================
# daewoon[i] = {
#     "start_age": int,
#     "end_age": int,
#     "pillar": str,
# }
DAEWOON_ITEM_KEYS = ["start_age", "end_age", "pillar"]
