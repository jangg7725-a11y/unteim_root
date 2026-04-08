# -*- coding: utf-8 -*-
"""상담 질문 → 주제(intent) 분류. 요약·프롬프트 우선순위 분기에 사용."""

from __future__ import annotations

from typing import Literal

CounselIntent = Literal[
    "personality",
    "wealth",
    "work",
    "relationship",
    "health",
    "exam",
    "general",
]

INTENT_LABEL_KO: dict[str, str] = {
    "personality": "성격·기질",
    "wealth": "재물·금전",
    "work": "직장·사업",
    "relationship": "인연·관계",
    "health": "건강·컨디션",
    "exam": "시험·합격·학업",
    "general": "일반",
}

# 프롬프트에 넣는「우선 설명할 분석 포인트」한 줄 요약
INTENT_FOCUS_POINTS: dict[str, str] = {
    "personality": (
        "일간·성향, 오행 균형, 격국, 십신 분포, 반복될 수 있는 패턴, 강점/주의점(요약에 기재된 범위 안에서)."
    ),
    "wealth": (
        "재성·식상·관성의 관계, 문서/손재·현금흐름 힌트(도메인), 운 흐름의 안정·변동, 오행 보완(용신 축)."
    ),
    "work": (
        "관성·식상·인성·재성의 균형, 승진·이직·사업 적합성에 연결될 수 있는 십신·격국, 대운·세운·월운 타이밍 발췌."
    ),
    "relationship": (
        "관성·재성, 십신상 관계·거리감 패턴, 신살·합충에 나온 힌트(있을 경우), 감정 기복이나 집착/안정 경향(요약 근거)."
    ),
    "health": (
        "오행 과다/부족, 과로·고갈·리듬(도메인·오행), 무리하기 쉬운 패턴. 의학 진단 대체 금지."
    ),
    "exam": (
        "인성·관성·식상(집중·압박·산출), 격국·용신, 세운·월운상 집중/결과에 연결될 수 있는 타이밍(요약 발췌)."
    ),
    "general": (
        "원국·오행·십신·용신·운 흐름을 균형 있게. 질문과 직접 연결되는 항목을 먼저 짧게 연결."
    ),
}

# 단정 완화 문구를 시스템에 추가할 intent (재물·건강·시험)
INTENTS_HEDGING = frozenset({"wealth", "health", "exam"})

HEDGING_RULES = """[이번 질문 주제에 대한 표현 주의]
재물·건강·시험/합격 가능성에 대해서는 아래를 지키세요.
- "~입니다"로 끝내는 단정 대신 「가능성이 있습니다」「이런 흐름이 보입니다」「조심하면 완화할 수 있습니다」 등 완화 표현을 씁니다.
- 의학·법률·투자 결과를 단정하지 마세요."""


def infer_counsel_intent(user_text: str) -> str:
    """
    질문 1차 분류. 더 구체적인 키워드(시험·건강 등)를 먼저 검사한다.
    반환: personality | wealth | work | relationship | health | exam | general
    """
    t = (user_text or "").strip().lower()
    if not t:
        return "general"

    # 시험·학업 (먼저)
    exam_kw = (
        "시험", "합격", "수능", "면접", "자격증", "공부", "입시", "학업", "공무원",
        "전공", "성적", "불합격", "재수", "논문",
    )
    if any(k in t for k in exam_kw):
        return "exam"

    # 건강 (단일 음절 '위'·'장' 등은 '직장' 등과 오매칭되므로 제외)
    health_kw = (
        "건강", "몸", "질병", "입원", "수술", "피로", "면역", "체력", "컨디션",
        "두통", "위장", "소화", "수면", "우울", "불면", "통증", "입맛", "소화불량",
    )
    if any(k in t for k in health_kw):
        return "health"

    # 재물
    wealth_kw = (
        "재물", "재산", "돈", "금전", "투자", "재테크", "손재", "수입", "저축",
        "부동산", "주식", "대출", "빚", "경제",
    )
    if any(k in t for k in wealth_kw):
        return "wealth"

    # 직장·사업
    work_kw = (
        "직장", "사업", "이직", "승진", "업무", "회사", "창업", "커리어", "퇴사",
        "상사", "동료", "프로젝트", "영업",
    )
    if any(k in t for k in work_kw):
        return "work"

    # 인연·관계 (직장 '관계'와 겹칠 수 있어 work 이후)
    rel_kw = (
        "연애", "결혼", "궁합", "인연", "배우자", "이혼", "남친", "여친", "소개팅",
        "썸", "짝사랑", "재회", "바람",
    )
    if any(k in t for k in rel_kw):
        return "relationship"

    # 성격
    pers_kw = (
        "성격", "성향", "기질", "장단점", "어떤 사람", "나는 어떤", "mbti", "성격이",
        "기질이", "성향이",
    )
    if any(k in t for k in pers_kw):
        return "personality"

    return "general"
