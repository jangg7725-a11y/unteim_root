# -*- coding: utf-8 -*-
"""상담 응답 → 요약 카드(JSON) — 핵심 흐름·주의·추천 행동."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

import requests

SUMMARY_CARD_SYSTEM = """당신은 상담 내용을 UI 카드용으로 짧게 정리하는 도우미입니다.
입력: 사용자 질문 + 상담가의 한국어 답변 전문.

출력은 반드시 **유효한 JSON 한 개**뿐이며, 키는 아래와 같습니다.
{
  "flow": "핵심 흐름·성향을 2~4문장으로 요약 (가능성·경향 중심)",
  "cautions": "주의할 점 1~2문장 (불안 조장·단정 금지, 의학·법률 단정 금지)",
  "actions": ["추천 행동 1", "추천 행동 2"]
}

규칙:
- 단정('반드시', '틀림없이', '무조건') 표현 금지. '~일 수 있습니다', '~경향이 보입니다' 등 완화.
- 불안·공포를 부추기는 표현 금지.
- actions는 실행 가능한 짧은 문장 2개 이하.
- JSON 외 설명·마크다운 금지."""


def _fallback_session_card(reply: str) -> Dict[str, Any]:
    """LLM 실패 시 최소 카드."""
    lines = [ln.strip() for ln in (reply or "").splitlines() if ln.strip()]
    snippet = " ".join(lines[:4])[:380].strip()
    if len(" ".join(lines)) > 380:
        snippet += "…"
    flow = snippet or "상담 내용을 바탕으로 천천히 적용해 보시면 좋습니다."
    return {
        "flow": flow,
        "cautions": "세부 판단은 본문을 함께 참고하고, 건강·법률·투자는 전문가 확인이 안전합니다.",
        "actions": ["한 가지 작은 실천부터 시도해 보기", "무리하지 않고 휴식·루틴 점검하기"],
    }


def generate_session_card(reply: str, user_question: str) -> Dict[str, Any]:
    """
    상담 답변을 바탕으로 요약 카드 생성.
    OpenAI 실패 시 규칙 기반 폴백.
    """
    reply = (reply or "").strip()
    user_question = (user_question or "").strip()
    if not reply:
        return _fallback_session_card("")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return _fallback_session_card(reply)

    base = (os.environ.get("OPENAI_API_BASE") or "https://api.openai.com/v1").rstrip("/")
    url = f"{base}/chat/completions"
    model = os.environ.get("OPENAI_SESSION_CARD_MODEL", os.environ.get("OPENAI_COUNSEL_MODEL", "gpt-4o-mini"))
    payload: Dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": SUMMARY_CARD_SYSTEM},
            {
                "role": "user",
                "content": f"질문:\n{user_question}\n\n상담 답변:\n{reply}",
            },
        ],
        "temperature": 0.35,
        "max_tokens": 500,
    }
    # json_object 미지원 모델은 400 반환 → 한 번 재시도
    payload["response_format"] = {"type": "json_object"}

    try:
        r = requests.post(
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=60,
        )
        if r.status_code == 400 and "response_format" in payload:
            del payload["response_format"]
            r = requests.post(
                url,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=60,
            )
        if r.status_code >= 400:
            return _fallback_session_card(reply)
        data = r.json()
        choices = data.get("choices") or []
        if not choices:
            return _fallback_session_card(reply)
        raw = (choices[0].get("message") or {}).get("content")
        if not isinstance(raw, str) or not raw.strip():
            return _fallback_session_card(reply)
        obj = json.loads(raw)
        flow = str(obj.get("flow", "")).strip()
        cautions = str(obj.get("cautions", "")).strip()
        actions_raw = obj.get("actions")
        actions: List[str] = []
        if isinstance(actions_raw, list):
            actions = [str(a).strip() for a in actions_raw if str(a).strip()][:2]
        if not flow:
            return _fallback_session_card(reply)
        if not cautions:
            cautions = "과도한 걱정보다는 작은 실천과 휴식을 병행해 보세요."
        if not actions:
            actions = ["오늘 할 일 한 가지만 정해 보기", "충분히 쉬고 내일 다시 읽어 보기"]
        return {"flow": flow, "cautions": cautions, "actions": actions}
    except Exception:
        return _fallback_session_card(reply)
