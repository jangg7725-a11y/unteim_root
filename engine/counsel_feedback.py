# engine/counsel_feedback.py
# -*- coding: utf-8 -*-
"""
상담 피드백 수집 (👍 / 👎)

저장: JSON 파일 (data/counsel_feedback.jsonl)
구조: 1줄 = 1 피드백 레코드 (JSONL)

API 서버에서 다음 엔드포인트를 연결한다:
  POST /api/counsel/feedback
  GET  /api/counsel/feedback/stats
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

_FEEDBACK_DIR = Path(__file__).parent.parent / "data" / "feedback"
_FEEDBACK_FILE = _FEEDBACK_DIR / "counsel_feedback.jsonl"


def _ensure_dir() -> None:
    _FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)


# ──────────────────────────────────────────────────
# 저장
# ──────────────────────────────────────────────────

def save_feedback(
    *,
    session_id: str,
    message_id: str,
    rating: str,                  # "up" | "down"
    counsel_intent: Optional[str] = None,
    character: Optional[str] = None,
    user_comment: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    피드백 1건을 JSONL 파일에 저장한다.

    Parameters
    ----------
    session_id    : 상담 세션 식별자 (클라이언트가 생성)
    message_id    : 피드백 대상 메시지 ID
    rating        : "up" (👍) 또는 "down" (👎)
    counsel_intent: 상담 인텐트 (personality/wealth/work/relationship/health/exam/general)
    character     : undol | unsuni
    user_comment  : 선택적 텍스트 코멘트
    meta          : 추가 메타 (예: 답변 길이, 응답시간 등)

    Returns
    -------
    저장된 레코드 dict
    """
    if rating not in ("up", "down"):
        raise ValueError(f"rating must be 'up' or 'down', got {rating!r}")

    record: Dict[str, Any] = {
        "ts": time.time(),
        "ts_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "session_id": str(session_id).strip(),
        "message_id": str(message_id).strip(),
        "rating": rating,
    }
    if counsel_intent:
        record["counsel_intent"] = counsel_intent
    if character:
        record["character"] = character
    if user_comment:
        record["user_comment"] = str(user_comment).strip()[:500]  # 최대 500자
    if meta:
        record["meta"] = meta

    # Render 무료 플랜은 재배포 시 파일시스템 초기화 — 파일 저장 실패해도 로그에는 남김
    try:
        _ensure_dir()
        with open(_FEEDBACK_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as write_err:
        import sys
        print(
            f"[FEEDBACK] 파일 저장 실패({write_err}) — 로그 백업: {json.dumps(record, ensure_ascii=False)}",
            file=sys.stderr,
        )

    return record


# ──────────────────────────────────────────────────
# 조회 / 통계
# ──────────────────────────────────────────────────

def load_all_feedback() -> List[Dict[str, Any]]:
    """전체 피드백 레코드 반환."""
    if not _FEEDBACK_FILE.exists():
        return []
    records = []
    with open(_FEEDBACK_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def get_feedback_stats() -> Dict[str, Any]:
    """
    전체 통계 반환.

    Returns
    -------
    {
        total: int,
        up: int,
        down: int,
        satisfaction_rate: float,   # up / total * 100
        by_intent: { intent: { up, down, total } },
        by_character: { character: { up, down } },
        recent_comments: [ { rating, comment, ts_iso } ]  # 최근 👎 코멘트 10건
    }
    """
    records = load_all_feedback()
    total = len(records)
    up = sum(1 for r in records if r.get("rating") == "up")
    down = total - up

    by_intent: Dict[str, Dict[str, int]] = {}
    by_character: Dict[str, Dict[str, int]] = {}
    recent_down_comments: List[Dict[str, Any]] = []

    for r in records:
        rating = r.get("rating", "")
        intent = r.get("counsel_intent", "unknown")
        char = r.get("character", "unknown")

        # 인텐트별
        if intent not in by_intent:
            by_intent[intent] = {"up": 0, "down": 0, "total": 0}
        by_intent[intent][rating] = by_intent[intent].get(rating, 0) + 1
        by_intent[intent]["total"] += 1

        # 캐릭터별
        if char not in by_character:
            by_character[char] = {"up": 0, "down": 0}
        by_character[char][rating] = by_character[char].get(rating, 0) + 1

        # 👎 코멘트 수집
        if rating == "down" and r.get("user_comment"):
            recent_down_comments.append({
                "rating": rating,
                "comment": r["user_comment"],
                "ts_iso": r.get("ts_iso", ""),
                "intent": intent,
            })

    # 최근 10건만
    recent_down_comments = sorted(
        recent_down_comments, key=lambda x: x["ts_iso"], reverse=True
    )[:10]

    return {
        "total": total,
        "up": up,
        "down": down,
        "satisfaction_rate": round(up / total * 100, 1) if total > 0 else 0.0,
        "by_intent": by_intent,
        "by_character": by_character,
        "recent_down_comments": recent_down_comments,
    }
