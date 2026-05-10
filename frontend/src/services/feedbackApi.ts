// frontend/src/services/feedbackApi.ts
// 상담 피드백 (👍 / 👎) API 클라이언트

import { getApiBase } from "./apiBase";

const API_BASE = getApiBase();

export type FeedbackRating = "up" | "down";

export type FeedbackRequest = {
  session_id: string;
  message_id: string;
  rating: FeedbackRating;
  counsel_intent?: string;
  character?: string;
  user_comment?: string;
};

export type FeedbackResponse = {
  ok: boolean;
  message_id: string;
  rating: FeedbackRating;
};

export async function postFeedback(
  body: FeedbackRequest
): Promise<FeedbackResponse> {
  const res = await fetch(`${API_BASE}/api/counsel/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    // 피드백 실패는 UX를 막지 않음 — 조용히 실패 허용
    console.warn("[feedbackApi] 피드백 저장 실패", res.status);
    return { ok: false, message_id: body.message_id, rating: body.rating };
  }

  const json = await res.json().catch(() => null);
  return {
    ok: true,
    message_id: body.message_id,
    rating: body.rating,
    ...(json ?? {}),
  };
}
