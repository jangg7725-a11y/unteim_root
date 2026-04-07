# engine/report_topic_registry.py
# -*- coding: utf-8 -*-
"""
질문형 추천 카테고리 레지스트리.
- 기본 리포트(총운·연간·월·오늘)와 선택형 확장 주제를 분리한다.
- selected_reports 최상위 키는 report_key(예: career, move, document)를 사용한다.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple

TopicTier = Literal["base", "extend", "planned"]

# 내부 키 → (한글 제목, tier)
TOPIC_DEFS: Dict[str, Tuple[str, TopicTier]] = {
    # 기본(항상 기본 PDF/분석 흐름에 포함 — selected_reports 에는 중복 생성 안 함)
    "total": ("총운", "base"),
    "annual": ("연간운", "base"),
    "monthly": ("월운", "base"),
    "daily": ("오늘의 운세", "base"),
    # 선택형 — 내러티브+엔진 힌트로 생성
    "career": ("직장운", "extend"),
    "money": ("재물운", "extend"),
    "relationship": ("인연운", "extend"),
    "compatibility": ("궁합", "extend"),
    "health": ("건강운", "extend"),
    "exam": ("합격운·시험운", "extend"),
    "travel_move": ("이직·이동운", "extend"),
    "marriage": ("결혼운", "extend"),
    "business": ("사업운", "extend"),
    "contract_doc": ("문서·계약운", "extend"),
    "noble": ("귀인운", "extend"),
    "accident_gossip": ("사고수·구설수", "extend"),
    "gaeunbeop": ("개운법", "extend"),
    "self_reflection": ("자기이해 리포트", "extend"),
}

# 레지스트리 id → API/result selected_reports 키 (기본은 동일, 예외만 매핑)
REGISTRY_ID_TO_REPORT_KEY: Dict[str, str] = {
    "travel_move": "move",
    "contract_doc": "document",
    "noble": "nobleman",
    "accident_gossip": "caution",
    "gaeunbeop": "opening",
}


def registry_id_to_report_key(registry_id: str) -> str:
    """레지스트리 내부 id → selected_reports 키."""
    return REGISTRY_ID_TO_REPORT_KEY.get(registry_id, registry_id)


def report_key_to_registry_id(report_key: str) -> Optional[str]:
    """selected_reports 키 → 레지스트리 id (역변환)."""
    if not report_key:
        return None
    if report_key in TOPIC_DEFS and TOPIC_DEFS[report_key][1] == "extend":
        return report_key
    rev = {v: k for k, v in REGISTRY_ID_TO_REPORT_KEY.items()}
    return rev.get(report_key)

# 한글/별칭 → 내부 키 (공백·슬래시 변형 허용)
ALIAS_TO_ID: Dict[str, str] = {
    "총운": "total",
    "연간운": "annual",
    "연간": "annual",
    "월운": "monthly",
    "월간": "monthly",
    "오늘의운세": "daily",
    "오늘의 운세": "daily",
    "오늘의운": "daily",
    "직장운": "career",
    "직장": "career",
    "재물운": "money",
    "재물": "money",
    "인연운": "relationship",
    "인연": "relationship",
    "궁합": "compatibility",
    "건강운": "health",
    "건강": "health",
    "합격운": "exam",
    "시험운": "exam",
    "시험": "exam",
    "이직운": "travel_move",
    "이동운": "travel_move",
    "이직": "travel_move",
    "이동": "travel_move",
    "결혼운": "marriage",
    "결혼": "marriage",
    "사업운": "business",
    "사업": "business",
    "문서운": "contract_doc",
    "계약운": "contract_doc",
    "문서": "contract_doc",
    "계약": "contract_doc",
    "귀인운": "noble",
    "귀인": "noble",
    "사고수": "accident_gossip",
    "구설수": "accident_gossip",
    "구설": "accident_gossip",
    "개운법": "gaeunbeop",
    "자기이해": "self_reflection",
    "자기이해리포트": "self_reflection",
    "자기이해 리포트": "self_reflection",
    "합격운시험운": "exam",
    "이직운이동운": "travel_move",
    "문서운계약운": "contract_doc",
    "사고수구설수": "accident_gossip",
}


def _norm_token(s: str) -> str:
    t = (s or "").strip()  # noqa: B008
    t = t.replace(" ", "").replace("/", "").replace("·", "")
    return t


def resolve_topic_id(token: str) -> Optional[str]:
    """사용자 입력 한 토큰을 내부 id로 변환."""
    raw = (token or "").strip()
    if not raw:
        return None
    if raw in TOPIC_DEFS:
        return raw
    n = _norm_token(raw)
    if n in ALIAS_TO_ID:
        return ALIAS_TO_ID[n]
    # 슬래시 포함 원문도 시도
    for k, v in ALIAS_TO_ID.items():
        if k.replace(" ", "") == n:
            return v
    return None


def normalize_selected_topics(
    raw: Optional[List[Any]],
    *,
    dedupe: bool = True,
) -> List[str]:
    """
    사용자가 고른 주제 목록을 내부 id로 정규화.
    알 수 없는 항목은 무시.
    """
    if not raw:
        return []
    out: List[str] = []
    seen: set[str] = set()
    for x in raw:
        tid = resolve_topic_id(str(x))
        if not tid:
            continue
        if dedupe:
            if tid in seen:
                continue
            seen.add(tid)
        out.append(tid)
    return out


def partition_topics(ids: List[str]) -> Tuple[List[str], List[str], List[str]]:
    """base / extend / planned 로 분리."""
    base, extend, planned = [], [], []
    for tid in ids:
        if tid not in TOPIC_DEFS:
            continue
        tier = TOPIC_DEFS[tid][1]
        if tier == "base":
            base.append(tid)
        elif tier == "extend":
            extend.append(tid)
        else:
            planned.append(tid)
    return base, extend, planned


def export_topic_catalog() -> Dict[str, Any]:
    """API/프론트용 카탈로그 스냅샷."""
    base = [{"id": k, "label": v[0], "report_key": k} for k, v in TOPIC_DEFS.items() if v[1] == "base"]
    extend = [
        {
            "id": k,
            "label": v[0],
            "report_key": registry_id_to_report_key(k),
        }
        for k, v in TOPIC_DEFS.items()
        if v[1] == "extend"
    ]
    return {
        "version": 2,
        "base_topics": base,
        "extend_topics": extend,
        "notes": {
            "base": "기본 리포트에 포함됨. selected_topics 에 넣어도 selected_reports 에는 중복 생성하지 않음.",
            "extend": "선택 시 selected_reports[report_key] 로 생성.",
        },
    }
