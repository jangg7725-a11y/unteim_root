# -*- coding: utf-8 -*-
"""
AI 상담 1턴: 사주 엔진(analyze_full) → 요약 → LLM.
후속 질문은 동일 생년월일로 엔진을 다시 돌려 같은 방식으로 요약을 갱신해 프롬프트에 포함한다.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, cast

import requests

from engine.counsel_intent import (
    HEDGING_RULES,
    INTENT_FOCUS_POINTS,
    INTENT_LABEL_KO,
    INTENTS_HEDGING,
    infer_counsel_intent,
)
from engine.counsel_summary import summarize_report_for_counsel
from engine.full_analyzer import analyze_full
from engine.sajuCalculator import calculate_saju
from engine.counsel_session_card import generate_session_card
from engine.shinsal_psychology_interpreter import get_shinsal_psychology_slots
from engine.twelve_fortunes_interpreter import get_fortune_stage_slots


# 톤: 사용자 질문 키워드로 추론 → 프롬프트에 주입
TONE_LINE = {
    "comfort": (
        "【말투】부드럽고 따뜻하게. 판단하지 않고, 곁에서 함께 짚어 주는 상담가처럼 말하세요."
    ),
    "serious": (
        "【말투】또박또박, 명확하게. 핵심 위주로 전달하되 차갑거나 냉소적으로 들리지 않게 하세요."
    ),
    "happy": (
        "【말투】밝고 희망적으로. 과장·단정 없이, 긍정의 여지와 여유를 열어 주세요."
    ),
}

SYSTEM_TEMPLATE = """당신은 20년 경력의 한국어 사주 상담가입니다.
단순 운세 나열이 아니라, 질문자와 마주 앉아 **코칭하듯** 대화합니다.

{tone_line}

{intent_block}

[절대 근거]
아래 「사주 분석 요약」은 운트임 엔진이 계산한 결과입니다. 설명·해석·원인·제안 모두 **이 요약 안의 내용을 우선 근거**로 삼으세요. 요약에 없는 구체적 사실(직업·결혼 시기 등)은 단정하지 말고 가능성·경향으로만 말하세요.
질문 주제와 직접 관련 없는 항목은 길게 늘어놓지 말고, **아래 [우선 설명할 분석 포인트]**와 연결되는 요약부터 짧게 인용하세요.

[금지]
- 사주와 무관한 일반론만 늘어놓기
- "조심하세요" 수준의 애매한 말만 반복하기
- 운세 항목만 나열하고 끝내기
- 절대적 예언·과장된 긍정/부정

[신뢰도·표현 보강 — 반드시 준수]
- 단정 금지: "반드시 ~입니다", "틀림없이", "무조건", "~할 것입니다(미래 단정)" 같은 표현을 쓰지 마세요.
- 가능성 중심: "~일 가능성이 있습니다", "~경향이 보입니다", "~하는 편이 이해에 도움이 될 수 있습니다" 등으로 서술하세요.
- 불안 유도 금지: 재앙·파국·망한다·큰일 등 공포·과장으로 불안을 키우는 표현을 쓰지 마세요. 필요하면 신중함을 **차분한 어조**로 전달하세요.
- 의학·법률·투자 결과를 단정하거나 진단·조언을 대신하지 마세요.

[필수 태도]
- 질문자 감정에 먼저 반응하고(공감), 그다음 사주로 연결하세요.
- 사용자 입장에서 이해되는 말로 풀어 쓰세요.
- 마지막에는 **지금 실천 가능한 행동**을 제안하세요.
- ②③에서는 반드시 **간지·오행·십신·격국·운 해설 등 요약에 실린 근거**를 한두 가지 짧게 짚고 넘어가세요(없으면 "요약에 명시 없음" 수준으로만).

[답변 구조 — 반드시 아래 순서·소제목을 사용]
① 공감: 질문·상황을 인정하고, "지금 그렇게 느끼실 수 있습니다"에 가까운 문장으로 시작합니다(1~3문장).
② 해석: **이번 질문 주제**와 맞닿는 흐름·성향을, 위 [우선 설명할 분석 포인트]와 연결해 짚습니다.
③ 원인: 왜 그런 패턴이 생길 수 있는지, **원국·오행·십신·운 흐름 등 요약에 나온 구조**와 연결해 설명합니다(일반론이 아니라 요약 근거).
④ 제안: 지금 단계에서 **구체적이고 작은 행동** 1~2가지를 제안합니다(실천 가능한 수준).

각 소제목은 반드시 "① 공감", "② 해석", "③ 원인", "④ 제안" 형식으로 시작하는 줄을 넣으세요.

[사주 분석 요약]
{analysis_summary}
"""


def _build_intent_block(intent: str) -> str:
    ik = intent if intent in INTENT_LABEL_KO else "general"
    label = INTENT_LABEL_KO[ik]
    focus = INTENT_FOCUS_POINTS[ik]
    lines = [
        "[이번 질문의 핵심 주제]",
        f"- 주제: {label} (intent={ik})",
        "",
        "[우선 설명할 분석 포인트]",
        f"- {focus}",
        "",
        "[서술 우선순위]",
        "- 아래 「사주 분석 요약」 블록에서, 위 포인트와 **먼저 맞닿는 문단**을 ② 해석에서 우선 인용하세요.",
        "- 질문과 거리가 먼 항목은 한두 문장 이하로 줄이거나 생략하세요.",
    ]
    if ik in INTENTS_HEDGING:
        lines.append("")
        lines.append(HEDGING_RULES)
    return "\n".join(lines)


def _infer_counsel_tone(user_text: str) -> str:
    """질문 톤에 맞춰 comfort / serious / happy 중 하나."""
    t = (user_text or "").strip()
    serious_kw = (
        "주의", "조심", "위험", "걱정", "불안", "무섭", "두렵", "절대", "반드시",
        "이별", "손해", "실패", "소송", "질병", "악화", "중대", "빚", "사고",
    )
    happy_kw = (
        "기쁨", "행복", "축하", "잘될", "기대", "설렘", "성공", "합격",
        "연애", "소개", "이직", "창업", "승진", "기회", "좋을까", "좋은지",
        "좋겠", "반갑",
    )
    comfort_kw = (
        "마음", "힘들", "외로", "슬프", "위로", "감정", "스트레스", "답답",
        "상처", "우울", "불안", "관계", "가족", "죄책",
    )
    if any(k in t for k in serious_kw):
        return "serious"
    if any(k in t for k in happy_kw):
        return "happy"
    if any(k in t for k in comfort_kw):
        return "comfort"
    return "comfort"


def _openai_chat_completion(messages: List[Dict[str, str]]) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("LLM_NOT_CONFIGURED")

    base = (os.environ.get("OPENAI_API_BASE") or "https://api.openai.com/v1").rstrip("/")
    url = f"{base}/chat/completions"
    model = os.environ.get("OPENAI_COUNSEL_MODEL", "gpt-4o-mini")
    payload = {
        "model": model,
        "messages": messages,
        "temperature": float(os.environ.get("OPENAI_COUNSEL_TEMPERATURE", "0.65")),
        "max_tokens": int(os.environ.get("OPENAI_COUNSEL_MAX_TOKENS", "1800")),
    }
    r = requests.post(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )
    if r.status_code >= 400:
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise RuntimeError(f"LLM_HTTP_{r.status_code}: {detail}")
    data = r.json()
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("LLM_EMPTY_CHOICES")
    content = (choices[0].get("message") or {}).get("content")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("LLM_EMPTY_CONTENT")
    return content.strip()


def _infer_counsel_style(user_text: str) -> tuple[str, str]:
    """(counselType hint, character id) — UI/TTS용 힌트."""
    t = user_text.strip()
    emo_kw = ("마음", "힘들", "불안", "외로", "슬프", "위로", "감정", "스트레스", "관계")
    if any(k in t for k in emo_kw):
        return "emotion", "unsuni"
    return "analysis", "undol"


def build_engine_analysis(
    birth_str: str,
    profile: Dict[str, Any],
    intent: str = "general",
) -> tuple[str, Dict[str, Any]]:
    pillars = calculate_saju(birth_str)
    report = analyze_full(cast(Any, pillars), birth_str=birth_str)
    if not isinstance(report, dict):
        raise RuntimeError("ENGINE_REPORT_INVALID")
    summary = summarize_report_for_counsel(report, profile=profile, intent=intent)
    return summary, report


def run_counsel_turn(
    *,
    birth_str: str,
    profile: Dict[str, Any],
    chat_messages: List[Dict[str, str]],
) -> Dict[str, Any]:
    """
    chat_messages: [{ "role": "user"|"assistant", "text": "..." }, ...]
    마지막 user 메시지가 현재 질문으로 간주된다.
    """
    if not chat_messages:
        raise ValueError("NO_MESSAGES")

    last_user = None
    for m in reversed(chat_messages):
        if m.get("role") == "user" and (m.get("text") or "").strip():
            last_user = (m.get("text") or "").strip()
            break
    if not last_user:
        raise ValueError("NO_USER_QUESTION")

    intent = infer_counsel_intent(last_user)
    analysis_summary, _report = build_engine_analysis(birth_str, profile, intent=intent)
    context: Dict[str, Any] = {}
    _sh = get_shinsal_psychology_slots(_report)
    if _sh["found"]:
        context["shinsal_dominant_trait"] = _sh["dominant_trait"]
        context["shinsal_behavior"] = _sh["behavior_pattern"]
        context["shinsal_caution"] = _sh["caution"]

    _tf = get_fortune_stage_slots(_report)
    if _tf["found"]:
        context["fortune_stage"] = _tf["label_ko"]
        context["fortune_core_energy"] = _tf["core_energy"]
        context["fortune_behavior"] = _tf["behavior_pattern"]
    tone_key = _infer_counsel_tone(last_user)
    tone_line = TONE_LINE.get(tone_key, TONE_LINE["comfort"])
    intent_block = _build_intent_block(intent)
    system_content = SYSTEM_TEMPLATE.format(
        analysis_summary=analysis_summary,
        tone_line=tone_line,
        intent_block=intent_block,
    )

    openai_messages: List[Dict[str, str]] = [{"role": "system", "content": system_content}]

    for m in chat_messages:
        role = m.get("role")
        text = (m.get("text") or "").strip()
        if not text or role not in ("user", "assistant"):
            continue
        openai_messages.append({"role": role, "content": text})

    reply = _openai_chat_completion(openai_messages)
    ctype, character = _infer_counsel_style(last_user)

    session_card = generate_session_card(reply, last_user)

    return {
        "reply": reply,
        "analysisSummary": analysis_summary,
        "context": context,
        "counselType": ctype,
        "character": character,
        "counselIntent": intent,
        "sessionCard": session_card,
    }
