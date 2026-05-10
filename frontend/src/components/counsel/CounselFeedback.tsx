// frontend/src/components/counsel/CounselFeedback.tsx
// 상담 메시지별 👍 / 👎 피드백 버튼

import { useState } from "react";
import { postFeedback, type FeedbackRating } from "@/services/feedbackApi";
import "./counsel-feedback.css";

type Props = {
  messageId: string;
  sessionId: string;
  counselIntent?: string;
  character?: string;
};

type FeedbackState = "idle" | "down_comment" | "done";

export function CounselFeedback({
  messageId,
  sessionId,
  counselIntent,
  character,
}: Props) {
  const [state, setState] = useState<FeedbackState>("idle");
  const [selected, setSelected] = useState<FeedbackRating | null>(null);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleRating(rating: FeedbackRating) {
    if (selected) return; // 이미 선택됨

    setSelected(rating);

    if (rating === "up") {
      // 👍 — 바로 저장, 완료 표시
      setSubmitting(true);
      await postFeedback({ session_id: sessionId, message_id: messageId, rating, counsel_intent: counselIntent, character });
      setSubmitting(false);
      setState("done");
    } else {
      // 👎 — 코멘트 입력창 열기
      setState("down_comment");
    }
  }

  async function handleCommentSubmit() {
    setSubmitting(true);
    await postFeedback({
      session_id: sessionId,
      message_id: messageId,
      rating: "down",
      counsel_intent: counselIntent,
      character,
      user_comment: comment.trim() || undefined,
    });
    setSubmitting(false);
    setState("done");
  }

  function handleCommentSkip() {
    postFeedback({
      session_id: sessionId,
      message_id: messageId,
      rating: "down",
      counsel_intent: counselIntent,
      character,
    });
    setState("done");
  }

  if (state === "done") {
    return (
      <div className="counsel-feedback counsel-feedback--done">
        <span className="counsel-feedback__thanks">
          {selected === "up" ? "👍 도움이 됐군요!" : "💬 피드백 감사해요"}
        </span>
      </div>
    );
  }

  if (state === "down_comment") {
    return (
      <div className="counsel-feedback counsel-feedback--comment">
        <p className="counsel-feedback__label">어떤 점이 아쉬웠나요? (선택)</p>
        <textarea
          className="counsel-feedback__textarea"
          placeholder="예: 너무 일반적인 답변이에요 / 내 상황과 맞지 않아요"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          rows={2}
          maxLength={200}
          disabled={submitting}
        />
        <div className="counsel-feedback__comment-actions">
          <button
            className="counsel-feedback__btn counsel-feedback__btn--skip"
            onClick={handleCommentSkip}
            disabled={submitting}
          >
            건너뛰기
          </button>
          <button
            className="counsel-feedback__btn counsel-feedback__btn--submit"
            onClick={handleCommentSubmit}
            disabled={submitting}
          >
            {submitting ? "저장 중…" : "보내기"}
          </button>
        </div>
      </div>
    );
  }

  // idle
  return (
    <div className="counsel-feedback">
      <span className="counsel-feedback__label">이 답변이 도움이 됐나요?</span>
      <button
        className={`counsel-feedback__icon${selected === "up" ? " selected" : ""}`}
        onClick={() => handleRating("up")}
        aria-label="도움됨"
        disabled={submitting}
      >
        👍
      </button>
      <button
        className={`counsel-feedback__icon${selected === "down" ? " selected" : ""}`}
        onClick={() => handleRating("down")}
        aria-label="아쉬움"
        disabled={submitting}
      >
        👎
      </button>
    </div>
  );
}
